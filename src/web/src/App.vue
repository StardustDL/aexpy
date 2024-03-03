<script setup lang="ts">
// This starter template is using Vue 3 <script setup> SFCs
// Check out https://v3.vuejs.org/api/sfc-script-setup.html#sfc-script-setup
import Layout from './pages/Layout.vue'
import { useRoute } from 'vue-router'
import { useStore } from './services/store'
import { NGlobalStyle, NBackTop, NConfigProvider, NSpin, NMessageProvider, useOsTheme, GlobalThemeOverrides, darkTheme, NLoadingBarProvider } from 'naive-ui'
import { zhCN, enUS, jaJP, ruRU, ukUA, idID, dateEnUS, dateJaJP, dateRuRU, dateUkUA, dateZhCN, dateIdID } from 'naive-ui'
import { watch, computed } from 'vue';
import { Chart, DoughnutController, Legend, Title, ArcElement, Tooltip, Decimation, Filler, LineController, CategoryScale, LinearScale, LineElement, PointElement, BarElement, BarController } from 'chart.js'
import hljs from 'highlight.js/lib/core';
import python from 'highlight.js/lib/languages/python'
import json from 'highlight.js/lib/languages/json'

const osThemeRef = useOsTheme();
const themeOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: "#196DB1FF",
    primaryColorHover: "#4381b3FF",
    primaryColorSuppl: "#4381b3FF",
    primaryColorPressed: "#114E80FF"
  }
}

Chart.register(DoughnutController, Legend, Title, ArcElement, Tooltip, Decimation, Filler, LineController, CategoryScale, LinearScale, LineElement, PointElement, BarController, BarElement);

const language = computed(() => {
  let lang = navigator.language;
  if (lang.indexOf("zh") != -1) {
    return {
      lang: zhCN,
      date: dateZhCN,
    };
  }
  if (lang.indexOf("ru") != -1) {
    return {
      lang: ruRU,
      date: dateRuRU,
    };
  }
  if (lang.indexOf("uk") != -1) {
    return {
      lang: ukUA,
      date: dateUkUA,
    };
  }
  if (lang.indexOf("ja") != -1) {
    return {
      lang: jaJP,
      date: dateJaJP,
    };
  }
  if (lang.indexOf("id") != -1) {
    return {
      lang: idID,
      date: dateIdID,
    };
  }
  return {
    lang: enUS,
    date: dateEnUS,
  };
});

hljs.registerLanguage('python', python);
hljs.registerLanguage('json', json);

hljs.registerLanguage('log', () => ({
  keywords: ["INFO", "DEBUG", "WARNING", "ERROR"],
  contains: [
    {
      className: 'number',
      begin: /\b\d{4}-\d{2}-\d{2},\d{2}:\d{2}:\d{2}\b/,
    },
    {
      className: 'string',
      begin: /\[(\w|\W)+:\d+:\w+\]/,
    },
  ]
}))
</script>

<template>
  <n-config-provider style="height: 100%" :theme="(osThemeRef == 'dark' ? darkTheme : null)"
    :theme-overrides="themeOverrides" :locale="language.lang" :date-locale="language.date" :hljs="hljs">
    <n-global-style />
    <n-message-provider>
      <n-loading-bar-provider>
        <suspense>
          <template #default>
            <Layout />
          </template>

          <template #fallback>
            <n-spin :size="80" id="loading-spin" />
          </template>
        </suspense>
      </n-loading-bar-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<style scoped>
#loading-spin {
  text-align: center;
  width: 100%;
  height: 100vh;
}
</style>

<style>
html,
body,
#app {
  height: 100%;
}
</style>