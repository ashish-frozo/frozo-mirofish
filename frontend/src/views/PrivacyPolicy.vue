<template>
  <div class="legal-page">
    <div class="legal-container">
      <router-link to="/" class="back-link">&larr; Back to Home</router-link>

      <div class="legal-banner">
        This is a template — please have it reviewed by legal counsel before launch.
      </div>

      <h1 class="legal-title">Privacy Policy</h1>
      <p class="legal-updated">Last updated: April 3, 2026</p>

      <section class="legal-section">
        <h2>1. Data We Collect</h2>
        <p>We collect the following categories of information:</p>
        <ul>
          <li><strong>Account information:</strong> Name, email address, and password hash when you create an account</li>
          <li><strong>Uploaded documents:</strong> Files you upload for analysis, including news articles, policy documents, and other seed data</li>
          <li><strong>Simulation data:</strong> Agent profiles, simulation configurations, generated reports, and prediction outputs</li>
          <li><strong>Usage data:</strong> Pages visited, features used, session duration, browser type, device information, and IP address</li>
          <li><strong>Payment information:</strong> Billing details processed through our payment provider (we do not store full card numbers)</li>
        </ul>
      </section>

      <section class="legal-section">
        <h2>2. How We Use Your Data</h2>
        <p>We use collected data to:</p>
        <ul>
          <li>Provide, maintain, and improve the Service</li>
          <li>Process your simulations and generate predictions</li>
          <li>Manage your account and process payments</li>
          <li>Send service-related communications and updates</li>
          <li>Monitor usage patterns to improve performance and user experience</li>
          <li>Detect and prevent fraud, abuse, or security incidents</li>
        </ul>
      </section>

      <section class="legal-section">
        <h2>3. Third-Party Services</h2>
        <p>We use the following third-party services that may process your data:</p>
        <ul>
          <li><strong>LLM Provider:</strong> Your uploaded content and simulation prompts are sent to our AI model provider for processing. Data is not used to train third-party models.</li>
          <li><strong>Neo4j:</strong> Knowledge graph storage for entity and relationship data extracted from your documents</li>
          <li><strong>Dodo Payments:</strong> Payment processing for subscription billing. Subject to their own privacy policy.</li>
          <li><strong>Sentry:</strong> Error tracking and performance monitoring. May collect anonymized usage and error data.</li>
          <li><strong>Resend:</strong> Transactional email delivery for account notifications and communications</li>
        </ul>
        <p>
          Each third-party service operates under its own privacy policy. We recommend reviewing their
          respective policies for details on their data handling practices.
        </p>
      </section>

      <section class="legal-section">
        <h2>4. Data Retention</h2>
        <p>
          We retain your account data for as long as your account is active. Uploaded documents and
          simulation data are retained for the duration of your subscription plus 30 days after account
          deletion to allow for data export. Usage logs are retained for up to 12 months. You may request
          earlier deletion at any time.
        </p>
      </section>

      <section class="legal-section">
        <h2>5. Your Rights</h2>
        <p>Depending on your jurisdiction, you may have the following rights:</p>
        <ul>
          <li><strong>Access:</strong> Request a copy of the personal data we hold about you</li>
          <li><strong>Correction:</strong> Request correction of inaccurate or incomplete personal data</li>
          <li><strong>Deletion:</strong> Request deletion of your personal data and account</li>
          <li><strong>Export:</strong> Request a machine-readable export of your data</li>
          <li><strong>Restriction:</strong> Request restriction of processing in certain circumstances</li>
          <li><strong>Objection:</strong> Object to processing based on legitimate interests</li>
        </ul>
        <p>
          To exercise any of these rights, contact us at
          <a href="mailto:privacy@augur.app">privacy@augur.app</a>.
          We will respond within 30 days.
        </p>
      </section>

      <section class="legal-section">
        <h2>6. Cookies and Tracking</h2>
        <p>
          We use essential cookies to maintain your session and authentication state. We may use
          analytics cookies to understand how the Service is used. You can control cookie preferences
          through your browser settings. The Service does not respond to "Do Not Track" signals at this time.
        </p>
      </section>

      <section class="legal-section">
        <h2>7. Children's Privacy</h2>
        <p>
          The Service is not intended for use by individuals under the age of 16. We do not knowingly
          collect personal data from children. If we become aware that we have collected data from a
          child under 16, we will take steps to delete such information promptly.
        </p>
      </section>

      <section class="legal-section">
        <h2>8. Changes to This Policy</h2>
        <p>
          We may update this Privacy Policy from time to time. We will notify you of material changes
          by posting the updated policy on this page and updating the "Last updated" date. Your continued
          use of the Service after changes are posted constitutes acceptance of the revised policy.
        </p>
      </section>

      <section class="legal-section">
        <h2>9. Contact</h2>
        <p>
          If you have questions about this Privacy Policy, please contact us at
          <a href="mailto:privacy@augur.app">privacy@augur.app</a>.
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
