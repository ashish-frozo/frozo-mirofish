<template>
  <div class="legal-page">
    <div class="legal-container">
      <router-link to="/" class="back-link">&larr; Back to Home</router-link>

      <div class="legal-banner">
        This is a template — please have it reviewed by legal counsel before launch.
      </div>

      <h1 class="legal-title">Terms of Service</h1>
      <p class="legal-updated">Last updated: April 3, 2026</p>

      <section class="legal-section">
        <h2>1. Acceptance of Terms</h2>
        <p>
          By accessing or using the Augur platform ("Service"), operated by MiroFish ("Company", "we", "us"),
          you agree to be bound by these Terms of Service. If you do not agree to these terms, you may not
          access or use the Service.
        </p>
      </section>

      <section class="legal-section">
        <h2>2. Account Registration</h2>
        <p>
          To use certain features of the Service, you must register for an account. You agree to provide
          accurate, current, and complete information during registration and to update such information
          to keep it accurate. You are responsible for safeguarding your account credentials and for all
          activities that occur under your account.
        </p>
      </section>

      <section class="legal-section">
        <h2>3. Acceptable Use</h2>
        <p>You agree not to:</p>
        <ul>
          <li>Use the Service for any unlawful purpose or in violation of any applicable laws</li>
          <li>Upload or transmit malicious code, viruses, or harmful data</li>
          <li>Attempt to gain unauthorized access to the Service or its related systems</li>
          <li>Interfere with or disrupt the integrity or performance of the Service</li>
          <li>Use the Service to generate content that is defamatory, harassing, or violates the rights of others</li>
          <li>Reverse engineer, decompile, or disassemble any part of the Service</li>
          <li>Resell or redistribute the Service without prior written consent</li>
        </ul>
      </section>

      <section class="legal-section">
        <h2>4. Intellectual Property</h2>
        <p>
          The Service, including its original content, features, and functionality, is owned by the Company
          and is protected by copyright, trademark, and other intellectual property laws. You retain ownership
          of any content you upload to the Service. By uploading content, you grant us a limited license to
          process and analyze it solely for the purpose of providing the Service.
        </p>
      </section>

      <section class="legal-section">
        <h2>5. AI-Generated Content Disclaimer</h2>
        <p>
          The Service uses artificial intelligence to generate predictions, simulations, and reports.
          AI-generated content is provided for informational purposes only and should not be considered
          as professional advice (financial, legal, medical, or otherwise). The Company makes no warranties
          regarding the accuracy, reliability, or completeness of AI-generated outputs. You are solely
          responsible for any decisions made based on such outputs.
        </p>
      </section>

      <section class="legal-section">
        <h2>6. Service Availability</h2>
        <p>
          We strive to maintain high availability of the Service but do not guarantee uninterrupted access.
          The Service may be temporarily unavailable due to maintenance, updates, or circumstances beyond
          our control. We reserve the right to modify, suspend, or discontinue any part of the Service
          at any time with reasonable notice.
        </p>
      </section>

      <section class="legal-section">
        <h2>7. Subscription and Billing</h2>
        <p>
          Certain features of the Service require a paid subscription. By subscribing, you agree to pay
          the applicable fees as described on our Pricing page. Subscriptions are billed on a recurring
          basis unless cancelled. Refunds are handled in accordance with our refund policy. We reserve
          the right to change pricing with 30 days' prior notice.
        </p>
      </section>

      <section class="legal-section">
        <h2>8. Limitation of Liability</h2>
        <p>
          To the maximum extent permitted by law, the Company shall not be liable for any indirect,
          incidental, special, consequential, or punitive damages, including but not limited to loss of
          profits, data, or goodwill, arising out of or related to your use of the Service. Our total
          liability shall not exceed the amount paid by you for the Service in the twelve (12) months
          preceding the claim.
        </p>
      </section>

      <section class="legal-section">
        <h2>9. Termination</h2>
        <p>
          We may terminate or suspend your account at any time for violation of these Terms or for any
          other reason at our sole discretion, with or without notice. Upon termination, your right to
          use the Service will cease immediately. You may terminate your account at any time by contacting
          us or using the account settings. Provisions that by their nature should survive termination
          shall survive.
        </p>
      </section>

      <section class="legal-section">
        <h2>10. Changes to Terms</h2>
        <p>
          We reserve the right to modify these Terms at any time. We will notify users of material changes
          by posting the updated Terms on this page and updating the "Last updated" date. Your continued
          use of the Service after changes are posted constitutes acceptance of the revised Terms.
        </p>
      </section>

      <section class="legal-section">
        <h2>11. Contact</h2>
        <p>
          If you have questions about these Terms of Service, please contact us at
          <a href="mailto:legal@augur.app">legal@augur.app</a>.
        </p>
      </section>
    </div>
  </div>
</template>

<script setup>
// Static legal page — no reactive state needed
</script>

<style scoped>
.legal-page {
  min-height: 100vh;
  background: #ffffff;
  padding: 40px 24px 80px;
  font-family: 'JetBrains Mono', monospace;
  color: #000;
}

.legal-container {
  max-width: 720px;
  margin: 0 auto;
}

.back-link {
  display: inline-block;
  color: #666;
  text-decoration: none;
  font-size: 14px;
  margin-bottom: 32px;
}

.back-link:hover {
  color: #000;
  text-decoration: underline;
}

.legal-banner {
  background: #f5f5f5;
  border: 1px solid #ddd;
  padding: 12px 16px;
  font-size: 13px;
  color: #666;
  margin-bottom: 32px;
}

.legal-title {
  font-size: 28px;
  font-weight: 700;
  margin: 0 0 8px;
}

.legal-updated {
  font-size: 13px;
  color: #999;
  margin: 0 0 40px;
}

.legal-section {
  margin-bottom: 32px;
}

.legal-section h2 {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 12px;
}

.legal-section p {
  font-size: 14px;
  line-height: 1.7;
  color: #333;
  margin: 0 0 12px;
}

.legal-section ul {
  padding-left: 24px;
  margin: 0 0 12px;
}

.legal-section li {
  font-size: 14px;
  line-height: 1.7;
  color: #333;
  margin-bottom: 6px;
}

.legal-section a {
  color: #000;
  text-decoration: underline;
}

.legal-section a:hover {
  color: #333;
}
</style>
