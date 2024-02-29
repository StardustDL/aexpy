<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NPageHeader, NFlex, NText, NA, NBreadcrumb, NSpin, NInput, NInputGroup, NIcon, NUpload, NUploadDragger, NLayoutContent, NAvatar, NStatistic, NTabs, NTabPane, NCard, NButton, useOsTheme, useMessage, useLoadingBar, UploadFileInfo } from 'naive-ui'
import { HomeIcon, RootIcon, GoIcon, UploadIcon } from '../components/icons'
import { useRoute, useRouter } from 'vue-router'
import HomeBreadcrumbItem from '../components/breadcrumbs/HomeBreadcrumbItem.vue'
import { useStore } from '../services/store'
import BuildStatus from '../components/BuildStatus.vue'
import PackageIndex from '../components/products/PackageIndex.vue'
import { Info } from '../models'
import { SessionStoragePackageApi } from '../services/api'

const store = useStore();
const router = useRouter();
const route = useRoute();
const message = useMessage();
const loadingbar = useLoadingBar();

const apiBaseUrl = ref(store.state.api.baseUrl);
const info = ref<Info>();

function onSetAPI() {
    store.commit('setApiUrl', apiBaseUrl.value);
    message.info(`API URL set to ${apiBaseUrl.value}`);
}

onMounted(async () => {
    loadingbar.start();
    try {
        info.value = await store.state.api.info();
        loadingbar.finish();
    }
    catch (e) {
        console.error(e);
        loadingbar.error();
        message.error(`Failed to load AexPy information.`);
    }
});

async function go(content: ArrayBuffer) {
    try {
        router.push({
            path: await SessionStoragePackageApi.uploadData(content),
        });
    }
    catch (e) {
        console.error(e);
        message.error("Failed to load uploaded data.");
    }
}

function onChange(options: { fileList: UploadFileInfo[] }) {
    if (options.fileList.length == 1 && options.fileList[0].file) {
        loadingbar.start();
        const file = options.fileList[0];
        const reader = new FileReader();
        reader.onload = function (e) {
            message.info(`The file has been uploaded: ${file.fullPath}`);
            loadingbar.finish();
            if (e.target!.result instanceof ArrayBuffer) {
                go(e.target!.result);
            } else {
                console.error(e.target!.result);
                message.error(`Failed to load data from the file.`);
            }
        };
        reader.onerror = function (e) {
            message.info(`Failed to upload file ${file.fullPath}: ${e.target?.error}`);
            loadingbar.error();
        };
        reader.readAsArrayBuffer(file.file!);
    }
}
</script>

<template>
    <n-flex vertical>
        <n-page-header @back="() => router.back()">
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
                <n-input-group size="large">
                    <n-input v-model:value="apiBaseUrl" placeholder="API Url" size="large" clearable>
                        <template #prefix>
                            <n-icon size="large" :component="RootIcon" />
                        </template>
                    </n-input>
                    <n-button type="primary" @click="onSetAPI" size="large">
                        <n-icon size="large" :component="GoIcon" />
                    </n-button>
                </n-input-group>
            </template>
        </n-page-header>

        <n-card title="Processed Packages" v-if="info" :bordered="false">
            <suspense>
                <template #default>
                    <PackageIndex />
                </template>
                <template #fallback>
                    <n-spin :size="80" />
                </template>
            </suspense>
        </n-card>
        <n-card title="View Processed File" v-if="info" :bordered="false">
            <n-upload @change="onChange" :show-file-list="false" :max="1">
                <n-upload-dragger>
                    <div style="margin-bottom: 12px">
                        <n-icon size="48" :depth="3" :component="UploadIcon" />
                    </div>
                    <n-text style="font-size: 16px">
                        Click or drag files produced by AexPy into this area to view
                    </n-text>
                </n-upload-dragger>
            </n-upload>
        </n-card>
        <n-card title="AexPy Information" v-if="info" :bordered="false">
            <BuildStatus :info="info"></BuildStatus>
        </n-card>
    </n-flex>
</template>
