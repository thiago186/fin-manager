// @ts-check
import withNuxt from './.nuxt/eslint.config.mjs';

export default withNuxt({
  rules: {
    // Import sorting rules
    'import/order': [
      'error',
      {
        groups: [
          'builtin', // Node.js built-in modules
          'external', // npm packages
          'internal', // Absolute imports
          ['parent', 'sibling'], // Relative imports
          'index', // ./
          'object', // object imports
          'type', // Types
        ],
        'newlines-between': 'always',
        alphabetize: {
          order: 'asc',
          caseInsensitive: true,
        },
      },
    ],
    'vue/html-self-closing': 'off',
  },
});