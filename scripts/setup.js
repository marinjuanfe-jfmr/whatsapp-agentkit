#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

console.log('\n╔════════════════════════════════════════╗');
console.log('║  whatsapp-agentkit Setup Wizard        ║');
console.log('║  Phase 2: Project Structure Setup      ║');
console.log('╚════════════════════════════════════════╝\n');

// Create directory structure
const dirs = [
  'src/agents',
  'src/transports',
  'src/messaging',
  'src/tools',
  'src/claude',
  'src/utils',
  'tests/agents',
  'tests/transports',
  'tests/tools',
  'config',
  'scripts',
];

console.log('📁 Creating directory structure...\n');

dirs.forEach((dir) => {
  const dirPath = path.join(__dirname, '..', dir);
  if (!fs.existsSync(dirPath)) {
    fs.mkdirSync(dirPath, { recursive: true });
    console.log(`  ✅ Created: ${dir}/`);
  }
});

// Create TypeScript configuration
const tsConfig = {
  compilerOptions: {
    target: 'ES2020',
    module: 'commonjs',
    lib: ['ES2020'],
    outDir: './dist',
    rootDir: './src',
    strict: true,
    esModuleInterop: true,
    skipLibCheck: true,
    forceConsistentCasingInFileNames: true,
    resolveJsonModule: true,
    declaration: true,
    declarationMap: true,
    sourceMap: true,
    types: ['node', 'jest'],
  },
  include: ['src/**/*'],
  exclude: ['node_modules', 'dist', 'tests'],
};

const tsConfigPath = path.join(__dirname, '..', 'tsconfig.json');
if (!fs.existsSync(tsConfigPath)) {
  fs.writeFileSync(tsConfigPath, JSON.stringify(tsConfig, null, 2));
  console.log('  ✅ Created: tsconfig.json');
}

// Create Jest configuration
const jestConfig = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  roots: ['<rootDir>/tests'],
  testMatch: ['**/__tests__/**/*.ts', '**/?(*.)+(spec|test).ts'],
  moduleFileExtensions: ['ts', 'js', 'json'],
  coveragePathIgnorePatterns: ['/node_modules/'],
};

const jestConfigPath = path.join(__dirname, '..', 'jest.config.js');
if (!fs.existsSync(jestConfigPath)) {
  fs.writeFileSync(
    jestConfigPath,
    `module.exports = ${JSON.stringify(jestConfig, null, 2)};`
  );
  console.log('  ✅ Created: jest.config.js');
}

// Create ESLint configuration
const eslintConfig = {
  env: {
    node: true,
    es2020: true,
  },
  extends: ['eslint:recommended'],
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaVersion: 2020,
    sourceType: 'module',
  },
  plugins: ['@typescript-eslint'],
  rules: {
    '@typescript-eslint/no-unused-vars': 'warn',
    '@typescript-eslint/explicit-function-return-types': 'off',
  },
};

const eslintConfigPath = path.join(__dirname, '..', '.eslintrc.json');
if (!fs.existsSync(eslintConfigPath)) {
  fs.writeFileSync(eslintConfigPath, JSON.stringify(eslintConfig, null, 2));
  console.log('  ✅ Created: .eslintrc.json');
}

// Create .gitignore
const gitignore = `
# Dependencies
node_modules/
/.pnp
.pnp.js

# Testing
/coverage

# Production
/dist
/build

# Misc
.DS_Store
.env
.env.local
.env.*.local
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*
lerna-debug.log*

# Editor directories and files
.vscode
.idea
*.suo
*.ntvs*
*.njsproj
*.sln
*.sw?

# Railway
.railway

# Generated
/generated
`;

const gitignorePath = path.join(__dirname, '..', '.gitignore');
if (!fs.existsSync(gitignorePath)) {
  fs.writeFileSync(gitignorePath, gitignore.trim());
  console.log('  ✅ Created: .gitignore');
}

// Create Prettier configuration
const prettierConfig = {
  semi: true,
  singleQuote: true,
  trailingComma: 'es5',
  printWidth: 80,
  tabWidth: 2,
};

const prettierConfigPath = path.join(__dirname, '..', '.prettierrc');
if (!fs.existsSync(prettierConfigPath)) {
  fs.writeFileSync(prettierConfigPath, JSON.stringify(prettierConfig, null, 2));
  console.log('  ✅ Created: .prettierrc');
}

// Create base files
console.log('\n📄 Creating base files...\n');

// Create index.ts
const indexTs = `import express from 'express';
import dotenv from 'dotenv';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());

// Webhook endpoint for incoming messages
app.post('/webhook', (req, res) => {
  console.log('Received webhook:', req.body);
  res.json({ success: true });
});

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

app.listen(PORT, () => {
  console.log(\`🚀 Server running on port \${PORT}\`);
  console.log(\`📍 Webhook: http://localhost:\${PORT}/webhook\`);
});
`;

const indexPath = path.join(__dirname, '..', 'src', 'index.ts');
if (!fs.existsSync(indexPath)) {
  fs.writeFileSync(indexPath, indexTs);
  console.log('  ✅ Created: src/index.ts');
}

// Create README for agents
const agentsReadme = `# Agents

Base agent implementations for whatsapp-agentkit.

## Structure

- \`BaseAgent.ts\` - Abstract base class for all agents
- \`AgentRegistry.ts\` - Registers and instantiates agents
- Each agent in its own directory

## Creating a New Agent

1. Create directory: \`src/agents/my-agent/\`
2. Create class extending \`BaseAgent\`
3. Register in \`AgentRegistry\`
4. Add tests in \`tests/agents/\`

## Example

\`\`\`typescript
import BaseAgent from '../BaseAgent';

export default class MyAgent extends BaseAgent {
  constructor() {
    super('my-agent', 'My Agent Description');
  }

  async handle(message: string): Promise<string> {
    // Handle incoming message
    return 'Response';
  }
}
\`\`\`
`;

const agentsReadmePath = path.join(__dirname, '..', 'src', 'agents', 'README.md');
if (!fs.existsSync(agentsReadmePath)) {
  fs.writeFileSync(agentsReadmePath, agentsReadme);
  console.log('  ✅ Created: src/agents/README.md');
}

console.log('\n' + '='.repeat(60));
console.log('\n✅ Phase 2: Project Structure Setup COMPLETE\n');
console.log('Directory structure and configuration files created.');
console.log('\n📋 Next steps:');
console.log('  1. Review configuration: npm run validate-config');
console.log('  2. Install dependencies: npm install');
console.log('  3. Proceed to Phase 3: WhatsApp Integration');
console.log('     → Start development server: npm run dev\n');
