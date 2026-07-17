"""
Script d'export et de restauration de la base de données PostgreSQL
Permet d'exporter la base générée (contrats, sinistres, visites, ...) pour la
réinstaller telle quelle sur une autre instance PostgreSQL.

Prérequis : les outils clients PostgreSQL (pg_dump, pg_restore) doivent être
installés et accessibles dans le PATH. Ils sont déjà présents dans l'image
Docker du projet (paquet postgresql-client).

Usage:
    python manage_database.py export --output backup.dump
    python manage_database.py restore --input backup.dump --host autre-serveur --dbname dwh --create-db
"""
import argparse
import os
import subprocess
import sys
from datetime import datetime

import psycopg2
from psycopg2 import sql

from app.config import settings


def build_env(password: str) -> dict:
    env = os.environ.copy()
    env["PGPASSWORD"] = password
    return env


def run_pg_tool(cmd: list, env: dict) -> int:
    try:
        result = subprocess.run(cmd, env=env)
        return result.returncode
    except FileNotFoundError:
        print(f"❌ Commande introuvable : {cmd[0]}. "
              f"Installez les outils clients PostgreSQL (paquet postgresql-client / postgresql).")
        sys.exit(1)


def export_database(args):
    output = args.output or f"{settings.DATABASE_NAME}_{datetime.now():%Y%m%d_%H%M%S}.dump"

    print(f"📦 Export de la base '{settings.DATABASE_NAME}' ({settings.DATABASE_HOST}:{settings.DATABASE_PORT})")
    print(f"   Fichier de sortie : {output}")

    cmd = [
        "pg_dump",
        "-h", settings.DATABASE_HOST,
        "-p", str(settings.DATABASE_PORT),
        "-U", settings.DATABASE_USER,
        "-d", settings.DATABASE_NAME,
        "-F", "c",  # format custom : compressé, compatible pg_restore
        "-f", output,
        "--no-owner",
        "--no-privileges",
    ]

    returncode = run_pg_tool(cmd, build_env(settings.DATABASE_PASSWORD))
    if returncode != 0:
        print("❌ Échec de l'export (voir le détail pg_dump ci-dessus)")
        sys.exit(returncode)

    size_mb = os.path.getsize(output) / (1024 * 1024)
    print(f"✅ Export terminé : {output} ({size_mb:.2f} Mo)")
    print("\nPour réinstaller cette base sur une autre instance PostgreSQL :")
    print(f"  python manage_database.py restore --input {output} --host <hote> --dbname <base> "
          f"--user <utilisateur> --password <mot_de_passe> --create-db")


def database_exists(host, port, user, password, dbname) -> bool:
    conn = psycopg2.connect(host=host, port=port, user=user, password=password, dbname="postgres")
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
            return cur.fetchone() is not None
    finally:
        conn.close()


def create_database(host, port, user, password, dbname):
    conn = psycopg2.connect(host=host, port=port, user=user, password=password, dbname="postgres")
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname)))
        print(f"✅ Base '{dbname}' créée sur {host}:{port}")
    finally:
        conn.close()


def restore_database(args):
    if not os.path.isfile(args.input):
        print(f"❌ Fichier introuvable : {args.input}")
        sys.exit(1)

    host = args.host or settings.DATABASE_HOST
    port = args.port or settings.DATABASE_PORT
    user = args.user or settings.DATABASE_USER
    password = args.password if args.password is not None else settings.DATABASE_PASSWORD
    dbname = args.dbname or settings.DATABASE_NAME

    print(f"📥 Restauration de '{args.input}' vers {host}:{port}/{dbname}")

    if not database_exists(host, port, user, password, dbname):
        if args.create_db:
            create_database(host, port, user, password, dbname)
        else:
            print(f"❌ La base '{dbname}' n'existe pas sur {host}:{port}. "
                  f"Relancez avec --create-db pour la créer automatiquement.")
            sys.exit(1)

    cmd = [
        "pg_restore",
        "-h", host,
        "-p", str(port),
        "-U", user,
        "-d", dbname,
        "--no-owner",
        "--no-privileges",
        "--clean",
        "--if-exists",
        args.input,
    ]
    if args.jobs and args.jobs > 1:
        cmd += ["-j", str(args.jobs)]

    returncode = run_pg_tool(cmd, build_env(password))
    if returncode != 0:
        print("⚠️  pg_restore a signalé des avertissements/erreurs (voir ci-dessus). Vérifiez le contenu de la base.")
        sys.exit(returncode)

    print(f"✅ Restauration terminée sur {host}:{port}/{dbname}")


def main():
    parser = argparse.ArgumentParser(
        description="Exporter la base de données générée ou la réinstaller sur une autre instance PostgreSQL"
    )
    subparsers = parser.add_subparsers(dest="command")

    export_parser = subparsers.add_parser(
        "export", help="Exporter la base courante (définie dans .env) dans un fichier"
    )
    export_parser.add_argument("--output", "-o", help="Chemin du fichier de sortie (défaut: <dbname>_<date>.dump)")

    restore_parser = subparsers.add_parser(
        "restore", help="Réinstaller un export sur une instance PostgreSQL"
    )
    restore_parser.add_argument("--input", "-i", required=True, help="Fichier de dump à restaurer")
    restore_parser.add_argument("--host", help="Hôte PostgreSQL cible (défaut: DATABASE_HOST du .env)")
    restore_parser.add_argument("--port", type=int, help="Port PostgreSQL cible (défaut: DATABASE_PORT du .env)")
    restore_parser.add_argument("--dbname", help="Nom de la base cible (défaut: DATABASE_NAME du .env)")
    restore_parser.add_argument("--user", help="Utilisateur PostgreSQL cible (défaut: DATABASE_USER du .env)")
    restore_parser.add_argument("--password", help="Mot de passe PostgreSQL cible (défaut: DATABASE_PASSWORD du .env)")
    restore_parser.add_argument("--create-db", action="store_true", help="Créer la base cible si elle n'existe pas")
    restore_parser.add_argument("--jobs", "-j", type=int, help="Nombre de jobs parallèles pour la restauration")

    args = parser.parse_args()

    if args.command == "export":
        export_database(args)
    elif args.command == "restore":
        restore_database(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
