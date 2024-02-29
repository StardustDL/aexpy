<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NPageHeader, NFlex, NText, NA, NBreadcrumb, NSpin, NInput, NInputGroup, NIcon, NUpload, NUploadDragger, NLayoutContent, NAvatar, NStatistic, NTabs, NTabPane, NCard, NButton, useOsTheme, useMessage, useLoadingBar } from 'naive-ui'
import { RootIcon } from '../components/icons'
import { useRoute, useRouter } from 'vue-router'
import HomeBreadcrumbItem from '../components/breadcrumbs/HomeBreadcrumbItem.vue'
import { useStore } from '../services/store'
import BuildStatus from '../components/BuildStatus.vue'
import NotFound from '../components/NotFound.vue'
import { Info } from '../models'
import { SessionStoragePackageApi } from '../services/api'

const store = useStore();
const router = useRouter();
const route = useRoute();
const message = useMessage();
const loadingbar = useLoadingBar();
const error = ref<boolean>(false);

const info = ref<Info>();

onMounted(async () => {
    try {
        info.value = await store.state.api.info();
    }
    catch (e) {
        console.error(e);
        message.error(`Failed to load AexPy information.`);
    }

    if (route.query.url) {
        message.info(`Loading data from ${route.query.url}`, {
            closable: true
        });
        loadingbar.start();
        try {
            let response = await fetch(route.query.url.toString());
            router.push({
                path: await SessionStoragePackageApi.uploadData(await response.arrayBuffer())
            });
            loadingbar.finish();
        } catch (e) {
            error.value = true;
            console.error(e);
            loadingbar.error();
            message.error(`Failed to load data from ${route.query.url}`);
        }
    }
});
</script>

<template>
    <n-flex vertical>
        <n-page-header @back="() => router.back()" :subtitle="'View'">
            <template #avatar>
                <n-avatar>
                    <n-icon :component="RootIcon" />
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
                <n-text>From {{ route.query.url }}</n-text>
            </template>
        </n-page-header>

        <NotFound v-if="error" :path="route.query.url?.toString() ?? ''"></NotFound>

        <n-spin v-else :size="80" style="width: 100%"></n-spin>
        <n-card title="AexPy Information" v-if="info" :bordered="false">
            <BuildStatus :info="info"></BuildStatus>
        </n-card>
    </n-flex>
</template>
