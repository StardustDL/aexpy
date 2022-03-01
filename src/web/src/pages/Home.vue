<script setup lang="ts">
import { ref, computed } from 'vue'
import { NPageHeader, NSpace, NText, NBreadcrumb, NInput, NInputGroup, NIcon, NLayoutContent, NAvatar, NStatistic, NTabs, NTabPane, NCard, NButton, useOsTheme, useMessage } from 'naive-ui'
import { HomeIcon, RootIcon, GoIcon } from '../components/icons'
import { useRouter } from 'vue-router'
import HomeBreadcrumbItem from '../components/breadcrumbs/HomeBreadcrumbItem.vue'
import { useStore } from '../services/store'

const store = useStore();
const router = useRouter();
const version = import.meta.env.PACKAGE_VERSION;
const message = useMessage();

const apiUrl = ref(store.state.api.baseUrl);

function onGo() {
    store.commit('setApiUrl', apiUrl.value);
    message.info(`API URL set to ${apiUrl.value}`);
}
</script>

<template>
    <n-page-header subtitle="Aexpy" @back="() => router.back()">
        <template #avatar>
            <n-avatar>
                <n-icon>
                    <RootIcon />
                </n-icon>
            </n-avatar>
        </template>
        <template #title>
            <n-text type="info">Aexpy</n-text>
        </template>
        <template #header>
            <n-breadcrumb>
                <HomeBreadcrumbItem />
            </n-breadcrumb>
        </template>
        <template #footer>
            <n-input-group>
                <n-input v-model:value="apiUrl" placeholder="API Url">
                    <template #prefix>
                        <n-icon size="large">
                            <RootIcon />
                        </n-icon>
                    </template>
                </n-input>
                <n-button type="primary" ghost @click="onGo">
                    <n-icon size="large">
                        <GoIcon />
                    </n-icon>
                </n-button>
            </n-input-group>
        </template>
    </n-page-header>
</template>
