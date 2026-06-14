#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const readline = require('readline');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
});

function question(prompt) {
  return new Promise((resolve) => {
    rl.question(prompt, (answer) => {
      resolve(answer.trim());
    });
  });
}

async function setupWhatsApp() {
  console.log('\n╔════════════════════════════════════════╗');
  console.log('║   WhatsApp Configuration Setup         ║');
  console.log('║   whatsapp-agentkit                    ║');
  console.log('╚════════════════════════════════════════╝\n');

  console.log('This wizard will help you configure WhatsApp for your bot.\n');

  // Step 1: Choose provider
  console.log('Step 1: Choose WhatsApp Provider');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
  console.log('Options:');
  console.log('  1) Whapi.io (Recommended - Simpler)');
  console.log('  2) Meta WhatsApp Business API (Enterprise)\n');

  let provider = '';
  while (!['1', '2'].includes(provider)) {
    provider = await question('Choose provider (1 or 2): ');
  }

  const isWhapi = provider === '1';
  const providerName = isWhapi ? 'Whapi.io' : 'Meta WhatsApp Business API';

  console.log(`\n✅ Selected: ${providerName}\n`);

  // Step 2: Get credentials
  console.log('Step 2: Enter Your Credentials');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

  let phoneNumber = '';
  while (!phoneNumber || phoneNumber.length < 10) {
    phoneNumber = await question(
      'Phone Number (with country code, e.g., 34123456789): '
    );
    if (phoneNumber.length < 10) {
      console.log('⚠️  Phone number must be at least 10 digits\n');
    }
  }

  let authToken = '';
  while (!authToken) {
    authToken = await question(
      isWhapi ? 'Whapi Token (from dashboard): ' : 'Meta Access Token: '
    );
    if (!authToken) {
      console.log('⚠️  Token cannot be empty\n');
    }
  }

  // Step 3: Additional settings for Meta
  let phoneNumberId = '';
  let businessAccountId = '';

  if (!isWhapi) {
    phoneNumberId = await question('Phone Number ID (optional): ');
    businessAccountId = await question('Business Account ID (optional): ');
  }

  // Step 4: Webhook URL (for later)
  console.log('\nStep 3: Webhook Configuration');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
  console.log('You will configure the webhook URL after deployment.');
  console.log(`Webhook Endpoint: https://your-domain.com/webhook\n`);

  // Step 5: Update .env file
  console.log('Step 4: Updating .env file');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

  const envPath = path.join(__dirname, '..', '.env');
  let envContent = fs.readFileSync(envPath, 'utf-8');

  // Parse existing env
  const envVars = {};
  envContent.split('\n').forEach((line) => {
    const trimmed = line.trim();
    if (trimmed && !trimmed.startsWith('#')) {
      const [key, ...valueParts] = trimmed.split('=');
      if (key) {
        envVars[key.trim()] = valueParts.join('=').trim();
      }
    }
  });

  // Update with new values
  envVars.WHATSAPP_PHONE_NUMBER = phoneNumber;
  envVars.WHATSAPP_AUTH_TOKEN = authToken;
  if (phoneNumberId) {
    envVars.WHATSAPP_PHONE_NUMBER_ID = phoneNumberId;
  }
  if (businessAccountId) {
    envVars.WHATSAPP_BUSINESS_ACCOUNT_ID = businessAccountId;
  }
  if (!envVars.WHATSAPP_PROVIDER) {
    envVars.WHATSAPP_PROVIDER = providerName;
  }

  // Write back .env
  let newEnvContent = '';
  for (const [key, value] of Object.entries(envVars)) {
    if (value) {
      newEnvContent += `${key}=${value}\n`;
    }
  }

  fs.writeFileSync(envPath, newEnvContent);

  // Step 6: Validate
  console.log('Validating configuration...\n');

  try {
    require('./validate-config.js');
  } catch (error) {
    // validate-config exits, so we won't reach here
  }

  rl.close();
}

setupWhatsApp().catch(console.error);
