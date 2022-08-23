<script setup lang="ts">
import { ref, computed } from 'vue'
import { NPageHeader, NSpace, NText, NA, NBreadcrumb, NInput, NInputGroup, NIcon, NLayoutContent, NAvatar, NStatistic, NTabs, NTabPane, NCard, NButton, useOsTheme, useMessage } from 'naive-ui'
import { HomeIcon, RootIcon, GoIcon, DataDirectoryIcon } from '../components/icons'
import { useRouter } from 'vue-router'
import HomeBreadcrumbItem from '../components/breadcrumbs/HomeBreadcrumbItem.vue'
import { useStore } from '../services/store'

const store = useStore();
const router = useRouter();
const message = useMessage();

const apiUrl = ref(store.state.api.baseUrl);

function onGo() {
    store.commit('setApiUrl', apiUrl.value);
    message.info(`API URL set to ${apiUrl.value}`);
}
</script>

<template>
    <n-space vertical>
        <n-page-header @back="() => router.back()">
            <template #avatar>
                <n-avatar>
                    <n-icon>
                        <RootIcon />
                    </n-icon>
                </n-avatar>
            </template>
            <template #title>
                <n-text type="info">AexPy</n-text>
            </template>
            <template #header>
                <n-breadcrumb>
                    <HomeBreadcrumbItem />
                </n-breadcrumb>
            </template>
            <template #footer>
                <n-input-group size="large">
                    <n-input v-model:value="apiUrl" placeholder="API Url" size="large" clearable>
                        <template #prefix>
                            <n-icon size="large">
                                <RootIcon />
                            </n-icon>
                        </template>
                    </n-input>
                    <n-button
                        type="primary"
                        :style="{ width: '2%' }"
                        size="large"
                        ghost
                        tag="a"
                        :href="store.state.api.baseUrl + '/data'"
                        target="_blank"
                    >
                        <n-icon size="large">
                            <DataDirectoryIcon />
                        </n-icon>
                    </n-button>
                    <n-button type="primary" @click="onGo" :style="{ width: '5%' }" size="large">
                        <n-icon size="large">
                            <GoIcon />
                        </n-icon>
                    </n-button>
                </n-input-group>
            </template>
        </n-page-header>

        <iframe
            :src="`${store.state.api.baseUrl}/data`"
            :style="{ 'border-width': '0px', 'width': '100%', 'height': '600px' }"
        ></iframe>
    </n-space>
</template>
