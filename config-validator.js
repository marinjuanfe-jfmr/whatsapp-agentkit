#!/usr/bin/env node

// Validate environment configuration for whatsapp-agentkit
const fs = require('fs');
const path = require('path');

// Load .env file manually
const envPath = path.join(__dirname, '.env');
if (fs.existsSync(envPath)) {
  const envContent = fs.readFileSync(envPath, 'utf-8');
  envContent.split('\n').forEach(line => {
    const trimmed = line.trim();
    if (trimmed && !trimmed.startsWith('#')) {
      const [key, ...valueParts] = trimmed.split('=');
      if (key && valueParts.length > 0) {
        process.env[key.trim()] = valueParts.join('=').trim();
      }
    }
  });
}

const REQUIRED_VARS = {
  ANTHROPIC_API_KEY: 'Claude API key from https://console.anthropic.com',
  WHATSAPP_PHONE_NUMBER: 'Bot WhatsApp phone number',
  PORT: 'Server port (default: 3000)',
};

const OPTIONAL_VARS = {
  NODE_ENV: 'Environment (development/production)',
  DEBUG: 'Debug logging pattern',
  LOG_LEVEL: 'Logging level (debug/info/warn/error)',
  WHATSAPP_AUTH_TOKEN: 'WhatsApp authentication token',
};

console.log('🔍 Validating whatsapp-agentkit configuration...\n');

let missingRequired = [];
let warnings = [];

// Check required variables
for (const [key, description] of Object.entries(REQUIRED_VARS)) {
  const value = process.env[key];
  if (!value || value === 'placeholder' || value.includes('your-')) {
    missingRequired.push(`  ❌ ${key}: ${description}`);
  } else {
    console.log(`  ✅ ${key}: configured`);
  }
}

// Check optional variables
for (const [key, description] of Object.entries(OPTIONAL_VARS)) {
  const value = process.env[key];
  if (!value) {
    console.log(`  ⚠️  ${key}: not set (optional)`);
  } else {
    console.log(`  ✅ ${key}: configured`);
  }
}

// Summary
console.log('\n' + '='.repeat(50));

if (missingRequired.length > 0) {
  console.log('\n❌ Configuration validation FAILED\n');
  console.log('Missing or invalid required variables:\n');
  missingRequired.forEach(msg => console.log(msg));
  console.log('\n✅ Next steps:');
  console.log('1. Copy .env.example to .env (if not already done)');
  console.log('2. Edit .env with your actual credentials');
  console.log('3. Obtain ANTHROPIC_API_KEY from https://console.anthropic.com');
  console.log('4. Obtain WHATSAPP credentials from your WhatsApp provider');
  console.log('5. Run this validator again: node config-validator.js\n');
  process.exit(1);
} else {
  console.log('\n✅ Configuration validation PASSED');
  console.log('\n✅ Ready to proceed to Phase 2: Project Structure Setup');
  console.log('Run: npm run setup\n');
  process.exit(0);
}
