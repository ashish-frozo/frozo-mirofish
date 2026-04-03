<template>
  <div id="app-wrapper">
    <router-view />
    <footer class="app-footer" v-if="showFooter">
      <router-link to="/terms">Terms of Service</router-link>
      <span class="separator">|</span>
      <router-link to="/privacy">Privacy Policy</router-link>
    </footer>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const showFooter = computed(() => {
  const footerRoutes = ['Home', 'Login', 'Signup', 'Dashboard', 'Pricing', 'Terms', 'Privacy']
  return footerRoutes.includes(route.name)
})
</script>

<style>
@import './assets/globals.css';

/* Global style reset */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  font-family: 'JetBrains Mono', 'Space Grotesk', 'Noto Sans SC', monospace;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #000000;
  background-color: #ffffff;
}

/* Scrollbar styles */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
}

::-webkit-scrollbar-thumb {
  background: #000000;
}

::-webkit-scrollbar-thumb:hover {
  background: #333333;
}

/* Global button styles */
button {
  font-family: inherit;
}

.app-footer {
  text-align: center;
  padding: 20px;
  font-size: 13px;
  color: #666;
  border-top: 1px solid #eee;
}
.app-footer a {
  color: #666;
  text-decoration: none;
}
.app-footer a:hover {
  color: #000;
  text-decoration: underline;
}
.app-footer .separator {
  margin: 0 8px;
}
</style>
