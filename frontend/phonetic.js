// Phonetic Search Implementation
// Using Soundex-like algorithm for French language

class PhoneticSearch {
    constructor() {
        // French phonetic rules
        this.rules = [
            // Silent letters at the end
            [/[aeioux]$/, ''],
            // H is always silent
            [/h/g, ''],
            // PH -> F
            [/ph/g, 'f'],
            // GN -> NI
            [/gn/g, 'ni'],
            // QU -> K
            [/qu/g, 'k'],
            // CH -> S
            [/ch/g, 's'],
            // C before E, I -> S
            [/c([ei])/g, 's$1'],
            // C before other -> K
            [/c/g, 'k'],
            // G before E, I -> J
            [/g([ei])/g, 'j$1'],
            // Y -> I
            [/y/g, 'i'],
            // Double consonants -> single
            [/([bcdfghjklmnpqrstvwxz])\1+/g, '$1'],
            // Remove accents
            [/[àâä]/g, 'a'],
            [/[éèêë]/g, 'e'],
            [/[îï]/g, 'i'],
            [/[ôö]/g, 'o'],
            [/[ùûü]/g, 'u'],
            [/ç/g, 's'],
            // Remove vowels except first
            [/([aeiou])[aeiou]+/g, '$1'],
        ];
    }

    // Convert a string to its phonetic code
    encode(str) {
        if (!str) return '';
        
        let code = str.toLowerCase().trim();
        
        // Apply all phonetic rules
        for (const [pattern, replacement] of this.rules) {
            code = code.replace(pattern, replacement);
        }
        
        // Keep only alphanumeric characters
        code = code.replace(/[^a-z0-9]/g, '');
        
        // Return first 4 characters padded with zeros
        return (code + '0000').substring(0, 4).toUpperCase();
    }

    // Compare two strings phonetically
    compare(str1, str2) {
        return this.encode(str1) === this.encode(str2);
    }

    // Search in an array of objects
    search(items, query, fields) {
        if (!query) return items;
        
        const queryCode = this.encode(query);
        
        return items.filter(item => {
            for (const field of fields) {
                const value = this.getNestedValue(item, field);
                if (value && this.encode(value) === queryCode) {
                    return true;
                }
            }
            return false;
        });
    }

    // Get nested object value by dot notation
    getNestedValue(obj, path) {
        return path.split('.').reduce((current, prop) => current?.[prop], obj);
    }

    // Fuzzy search with similarity score
    fuzzySearch(items, query, fields, threshold = 0.6) {
        if (!query) return items;
        
        const queryCode = this.encode(query);
        const queryLower = query.toLowerCase();
        
        return items
            .map(item => {
                let maxScore = 0;
                
                for (const field of fields) {
                    const value = this.getNestedValue(item, field);
                    if (!value) continue;
                    
                    const valueLower = value.toLowerCase();
                    const valueCode = this.encode(value);
                    
                    // Exact match
                    if (valueLower === queryLower) {
                        maxScore = Math.max(maxScore, 1.0);
                    }
                    // Phonetic match
                    else if (valueCode === queryCode) {
                        maxScore = Math.max(maxScore, 0.9);
                    }
                    // Contains
                    else if (valueLower.includes(queryLower)) {
                        maxScore = Math.max(maxScore, 0.8);
                    }
                    // Starts with
                    else if (valueLower.startsWith(queryLower)) {
                        maxScore = Math.max(maxScore, 0.7);
                    }
                    // Levenshtein distance
                    else {
                        const distance = this.levenshtein(queryLower, valueLower);
                        const similarity = 1 - (distance / Math.max(queryLower.length, valueLower.length));
                        maxScore = Math.max(maxScore, similarity);
                    }
                }
                
                return { item, score: maxScore };
            })
            .filter(result => result.score >= threshold)
            .sort((a, b) => b.score - a.score)
            .map(result => result.item);
    }

    // Levenshtein distance algorithm
    levenshtein(str1, str2) {
        const m = str1.length;
        const n = str2.length;
        const dp = Array(m + 1).fill(null).map(() => Array(n + 1).fill(0));
        
        for (let i = 0; i <= m; i++) dp[i][0] = i;
        for (let j = 0; j <= n; j++) dp[0][j] = j;
        
        for (let i = 1; i <= m; i++) {
            for (let j = 1; j <= n; j++) {
                if (str1[i - 1] === str2[j - 1]) {
                    dp[i][j] = dp[i - 1][j - 1];
                } else {
                    dp[i][j] = Math.min(
                        dp[i - 1][j] + 1,     // deletion
                        dp[i][j - 1] + 1,     // insertion
                        dp[i - 1][j - 1] + 1  // substitution
                    );
                }
            }
        }
        
        return dp[m][n];
    }

    // Highlight matching text
    highlight(text, query) {
        if (!text || !query) return text;
        
        const regex = new RegExp(`(${query})`, 'gi');
        return text.replace(regex, '<mark>$1</mark>');
    }
}

// Create global phonetic search instance
const phoneticSearch = new PhoneticSearch();

// Test examples
if (typeof window !== 'undefined' && window.location.hostname === 'localhost') {
    // Test French phonetic encoding
    const testCases = [
        ['Martin', 'Marten'],    // Should match phonetically
        ['Dupont', 'Dupond'],    // Should match phonetically
        ['François', 'Francois'], // Should match phonetically
        ['Bernard', 'Bernar'],   // Should match phonetically
        ['Lefèvre', 'Lefevre'],  // Should match phonetically
    ];
    
    console.log('🔍 Phonetic Search Test Cases:');
    testCases.forEach(([str1, str2]) => {
        const code1 = phoneticSearch.encode(str1);
        const code2 = phoneticSearch.encode(str2);
        const match = code1 === code2;
        console.log(`  ${str1} (${code1}) ${match ? '✓' : '✗'} ${str2} (${code2})`);
    });
}
