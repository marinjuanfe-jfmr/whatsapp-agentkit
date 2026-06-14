#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

// Load .env file manually
const envPath = path.join(__dirname, '..', '.env');
if (fs.existsSync(envPath)) {
  const envContent = fs.readFileSync(envPath, 'utf-8');
  envContent.split('\n').forEach((line) => {
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
  WHATSAPP_AUTH_TOKEN: 'WhatsApp authentication token',
  PORT: 'Server port (default: 3000)',
};

const OPTIONAL_VARS = {
  NODE_ENV: 'Environment (development/production)',
  DEBUG: 'Debug logging pattern',
  LOG_LEVEL: 'Logging level (debug/info/warn/error)',
  WHATSAPP_PROVIDER: 'WhatsApp provider (Whapi.io or Meta)',
  WHATSAPP_PHONE_NUMBER_ID: 'Phone Number ID (for Meta API)',
  WHATSAPP_BUSINESS_ACCOUNT_ID: 'Business Account ID (for Meta API)',
};

console.log('🔍 Validating whatsapp-agentkit configuration...\n');

let missingRequired = [];
let warnings = [];

// Check required variables
for (const [key, description] of Object.entries(REQUIRED_VARS)) {
  const value = process.env[key];
  if (
    !value ||
    value === 'placeholder' ||
    value.includes('your-') ||
    value.includes('xxx')
  ) {
    missingRequired.push(`  ❌ ${key}: ${description}`);
  } else {
    // Mask sensitive values
    const masked =
      key === 'WHATSAPP_AUTH_TOKEN'
        ? value.substring(0, 10) + '****'
        : value;
    console.log(`  ✅ ${key}: ${masked}`);
  }
}

// Check optional variables
for (const [key, description] of Object.entries(OPTIONAL_VARS)) {
  const value = process.env[key];
  if (!value) {
    console.log(`  ⚠️  ${key}: not set (optional)`);
  } else {
    const masked =
      key === 'WHATSAPP_AUTH_TOKEN'
        ? value.substring(0, 10) + '****'
        : value;
    console.log(`  ✅ ${key}: ${masked}`);
  }
}

// Summary
console.log('\n' + '='.repeat(60));

if (missingRequired.length > 0) {
  console.log('\n❌ Configuration validation FAILED\n');
  console.log('Missing or invalid required variables:\n');
  missingRequired.forEach((msg) => console.log(msg));
  console.log('\n📖 Setup Instructions:');
  console.log('1. Read: WHATSAPP_SETUP.md for detailed instructions');
  console.log('2. Option A: Run interactive setup');
  console.log('   $ node scripts/setup-whatsapp.js');
  console.log('3. Option B: Edit .env manually');
  console.log('   $ nano .env   # or your favorite editor');
  console.log('4. Run validator again: npm run validate-config\n');
  process.exit(1);
} else {
  console.log('\n✅ Configuration validation PASSED\n');
  console.log('All required variables are configured correctly.');
  console.log('You are ready to proceed to Phase 2: Project Structure Setup\n');
  console.log('Next: npm run setup\n');
  process.exit(0);
}
