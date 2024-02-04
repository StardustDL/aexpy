<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NPageHeader, NSpace, NText, NA, NBreadcrumb, NInput, NInputGroup, NIcon, NUpload, NUploadDragger, NLayoutContent, NAvatar, NStatistic, NTabs, NTabPane, NCard, NButton, useOsTheme, useMessage, useLoadingBar, UploadFileInfo } from 'naive-ui'
import { HomeIcon, RootIcon, GoIcon, DataDirectoryIcon, UploadIcon } from '../components/icons'
import { useRouter } from 'vue-router'
import HomeBreadcrumbItem from '../components/breadcrumbs/HomeBreadcrumbItem.vue'
import { useStore } from '../services/store'
import BuildStatus from '../components/BuildStatus.vue'
import { Info, ProduceMode } from '../models'

const store = useStore();
const router = useRouter();
const message = useMessage();
const loadingbar = useLoadingBar();

const info = ref<Info>();

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

function go(content: string) {
    let data = JSON.parse(content);
    let id = "data@uploaded";
    window.sessionStorage.setItem(id, content);
    let path = '/'
    if ("release" in data) {
        path = `/distribution/${id}`;
    } else if ("distribution" in data) {
        path = `/description/${id}`;
    } else if ("entries" in data) {
        path = `/difference/${id}`;
    } else {
        path = `/report/${id}`;
    }
    router.push({
        path: path,
        query: {
            mode: ProduceMode.Read
        }
    });
}

function onChange(options: { fileList: UploadFileInfo[] }) {
    if (options.fileList.length == 1 && options.fileList[0].file) {
        loadingbar.start();
        const file = options.fileList[0];
        const reader = new FileReader();
        reader.onload = function (e) {
            message.info(`The file has been uploaded: ${file.fullPath}`);
            loadingbar.finish();
            go(e.target!.result?.toString() || "");
        };
        reader.onerror = function (e) {
            message.info(`Failed to upload file ${file.fullPath}: ${e.target?.error}`);
            loadingbar.error();
        };
        reader.readAsText(file.file!, "utf-8");
    }
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
                <n-upload @change="onChange" :show-file-list="false" :max="1">
                    <n-upload-dragger>
                        <div style="margin-bottom: 12px">
                            <n-icon size="48" :depth="3">
                                <upload-icon />
                            </n-icon>
                        </div>
                        <n-text style="font-size: 16px">
                            Click or drag files produced by AexPy into this area to view
                        </n-text>
                    </n-upload-dragger>
                </n-upload>
            </template>
        </n-page-header>

        <n-card title="AexPy Information" hoverable embedded v-if="info">
            <BuildStatus :info="info"></BuildStatus>
        </n-card>


    </n-space>
</template>
