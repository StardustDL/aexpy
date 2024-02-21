<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NPageHeader, NFlex, NInput, NTooltip, NInputGroup, NDivider, NInputGroupLabel, NCollapseTransition, NCode, NText, NButtonGroup, NBreadcrumb, NIcon, NLayoutContent, useLoadingBar, NAvatar, NLog, NSwitch, NStatistic, NTabs, NTabPane, NCard, NButton, useOsTheme, useMessage, NDescriptions, NDescriptionsItem, NSpin, NDrawer, NDrawerContent } from 'naive-ui'
import { HomeIcon, RootIcon, LinkIcon, DistributionIcon, GoIcon, DescriptionIcon, LogIcon, PreprocessIcon, FileIcon } from '../../components/icons'
import { useRouter, useRoute } from 'vue-router'
import HomeBreadcrumbItem from '../../components/breadcrumbs/HomeBreadcrumbItem.vue'
import ProjectBreadcrumbItem from '../../components/breadcrumbs/ProjectBreadcrumbItem.vue'
import ReleaseBreadcrumbItem from '../../components/breadcrumbs/ReleaseBreadcrumbItem.vue'
import { useStore } from '../../services/store'
import { Distribution, Release } from '../../models'
import NotFound from '../../components/NotFound.vue'
import MetadataViewer from '../../components/metadata/MetadataViewer.vue'
import DistributionViewer from '../../components/products/DistributionViewer.vue'
import { publicVars, apiUrl } from '../../services/utils'
import DistributionSwitch from '../../components/switches/DistributionSwitch.vue'
import LogSwitch from '../../components/switches/LogSwitch.vue'

const store = useStore();
const router = useRouter();
const route = useRoute();
const message = useMessage();
const loadingbar = useLoadingBar();

const params = route.params as {
    project?: string,
    version?: string,
};
const release = new Release(params.project, params.version);

const showDists = ref<boolean>(true);

const data = ref<Distribution>();
const error = ref<boolean>(false);
const showLog = ref<boolean>(false);
const logContent = ref<string>();

onMounted(async () => {
    loadingbar.start();
    try {
        data.value = await store.state.api.distribution(release);
        publicVars({ "data": data.value });
    }
    catch (e) {
        console.error(e);
        error.value = true;
        message.error(`Failed to load preprocessed data for ${release}.`);
    }

    if (error.value) {
        loadingbar.error();
    }
    else {
        loadingbar.finish();
    }
});

async function onLog(value: boolean) {
    if (!value || logContent.value) return;
    try {
        logContent.value = await store.state.api.apiLog(release);
        publicVars({ "log": logContent.value });
    }
    catch {
        message.error(`Failed to load log for ${release}.`);
    }
}
</script>

<template>
    <n-flex vertical>
        <n-page-header :title="release?.toString() ?? 'Unknown'" subtitle="Distribution" @back="() => router.back()">
            <template #avatar>
                <n-avatar>
                    <n-icon :component="PreprocessIcon" />
                </n-avatar>
            </template>
            <template #header>
                <n-breadcrumb>
                    <HomeBreadcrumbItem />
                    <ProjectBreadcrumbItem />
                    <ReleaseBreadcrumbItem :release="release" />
                </n-breadcrumb>
            </template>
            <template #footer>
                <n-flex v-if="data">
                    <MetadataViewer :data="data" />
                    <n-button-group size="small" v-if="release">
                        <n-button tag="a" :href="apiUrl(release)" type="info" ghost>
                            <n-icon size="large" :component="DescriptionIcon" />
                        </n-button>
                    </n-button-group>
                    <DistributionSwitch v-model="showDists" />
                    <LogSwitch v-model="showLog" @update="onLog" />
                </n-flex>
            </template>
        </n-page-header>

        <NotFound v-if="error" :path="router.currentRoute.value.fullPath"></NotFound>
        <n-spin v-else-if="!data" :size="80" style="width: 100%"></n-spin>

        <n-flex v-if="data" vertical>
            <n-collapse-transition :show="showDists">
                <n-divider>
                    <n-flex :wrap="false" :align="'center'">
                        <n-icon size="large" :component="DistributionIcon" />
                        Distribution
                    </n-flex>
                </n-divider>
                <DistributionViewer :data="data" />
            </n-collapse-transition>
        </n-flex>

        <n-drawer v-model:show="showLog" :width="600" placement="right" v-if="data">
            <n-drawer-content title="Log" :native-scrollbar="false">
                <n-spin v-if="logContent == undefined" :size="60" style="width: 100%"></n-spin>
                <n-log v-else :log="logContent" :rows="40" language="log"></n-log>
            </n-drawer-content>
        </n-drawer>
    </n-flex>
</template>
