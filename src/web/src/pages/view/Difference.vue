<script setup lang="ts">
import { ref, computed, onMounted, h } from 'vue'
import { NPageHeader, NFlex, NTooltip, NButtonGroup, NBreadcrumb, NModal, NIcon, useLoadingBar, NAvatar, NLog, NSwitch, NButton, useMessage, NSpin, NDrawer, NDrawerContent } from 'naive-ui'
import { HomeIcon, RootIcon, DistributionIcon, DescriptionIcon, LogIcon, DiffIcon, ReportIcon, CountIcon, EvaluateIcon } from '../../components/icons'
import { useRouter, useRoute } from 'vue-router'
import HomeBreadcrumbItem from '../../components/breadcrumbs/HomeBreadcrumbItem.vue'
import ProjectBreadcrumbItem from '../../components/breadcrumbs/ProjectBreadcrumbItem.vue'
import ReleasePairBreadcrumbItem from '../../components/breadcrumbs/ReleasePairBreadcrumbItem.vue'
import { useStore } from '../../services/store'
import { ApiDifference, ReleasePair, Release, Report } from '../../models'
import NotFound from '../../components/NotFound.vue'
import MetadataViewer from '../../components/metadata/MetadataViewer.vue'
import ApiDifferenceViewer from '../../components/products/ApiDifferenceViewer.vue'
import { publicVars, apiUrl, distributionUrl, reportUrl } from '../../services/utils'
import DistributionSwitch from '../../components/switches/DistributionSwitch.vue'
import LogSwitch from '../../components/switches/LogSwitch.vue'
import StaticticsSwitch from '../../components/switches/StatisticsSwitch.vue'

const store = useStore();
const router = useRouter();
const route = useRoute();
const message = useMessage();
const loadingbar = useLoadingBar();

const params = route.params as {
    project?: string,
    old?: string,
    new?: string,
};
const release = new ReleasePair(new Release(params.project, params.old), new Release(params.project, params.new));

console.log(route.query.entry)

const showDists = ref<boolean>(false);
const showStats = ref<boolean>(true);
const showReport = ref<boolean>(false);

const data = ref<ApiDifference>();
const error = ref<boolean>(false);
const showLog = ref<boolean>(false);
const logContent = ref<string>();
const reportData = ref<Report>();

onMounted(async () => {
    loadingbar.start();
    try {
        data.value = await store.state.api.change(release);
        publicVars({ "data": data.value });
    }
    catch (e) {
        console.error(e);
        error.value = true;
        message.error(`Failed to load data for ${release}.`);
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
        logContent.value = await store.state.api.changeLog(release);
        publicVars({ "log": logContent.value });
    }
    catch {
        message.error(`Failed to load log for ${release}.`);
    }
}

async function onReport(value: boolean) {
    if (!value || reportData.value) return;
    try {
        reportData.value = await store.state.api.report(release);
        publicVars({ "report": reportData.value });
    }
    catch {
        message.error(`Failed to load report for ${release}.`);
    }
}
</script>

<template>
    <n-flex vertical>
        <n-page-header :title="release?.toString() ?? 'Unknown'" subtitle="API Difference" @back="() => router.back()">
            <template #avatar>
                <n-avatar>
                    <n-icon :component="DiffIcon" />
                </n-avatar>
            </template>
            <template #header>
                <n-breadcrumb>
                    <HomeBreadcrumbItem />
                    <ProjectBreadcrumbItem />
                    <ReleasePairBreadcrumbItem :release="release" />
                </n-breadcrumb>
            </template>
            <template #footer>
                <n-flex v-if="data">
                    <MetadataViewer :data="data" />
                    <n-button-group size="small" v-if="release">
                        <n-button tag="a" :href="distributionUrl(release.old)" type="info" ghost>
                            <n-icon size="large" :component="DistributionIcon" />
                        </n-button>
                        <n-button tag="a" :href="apiUrl(release.old)" type="info" ghost>
                            <n-icon size="large" :component="DescriptionIcon" />
                        </n-button>
                        <n-button tag="a" :href="distributionUrl(release.new)" type="info" ghost>
                            <n-icon size="large" :component="DistributionIcon" />
                        </n-button>
                        <n-button tag="a" :href="apiUrl(release.new)" type="info" ghost>
                            <n-icon size="large" :component="DescriptionIcon" />
                        </n-button>
                        <n-button tag="a" :href="reportUrl(release)" type="info" ghost>
                            <n-icon size="large" :component="ReportIcon" />
                        </n-button>
                    </n-button-group>
                    <DistributionSwitch v-model="showDists" />
                    <StaticticsSwitch v-model="showStats" />
                    <n-tooltip>
                        <template #trigger>
                            <n-switch v-model:value="showReport" @update-value="onReport">
                                <template #checked>
                                    <n-icon size="large" :component="ReportIcon" />
                                </template>
                                <template #unchecked>
                                    <n-icon size="large" :component="ReportIcon" />
                                </template>
                            </n-switch>
                        </template>
                        Report
                    </n-tooltip>
                    <LogSwitch v-model="showLog" @update="onLog" />
                </n-flex>
            </template>
        </n-page-header>

        <NotFound v-if="error" :path="router.currentRoute.value.fullPath"></NotFound>
        <n-spin v-else-if="!data" :size="80" style="width: 100%"></n-spin>

        <ApiDifferenceViewer v-if="data" :data="data" :show-stats="showStats" :show-dists="showDists" :entry="route.query.entry ? route.query.entry.toString() : undefined"/>

        <n-modal v-model:show="showReport" preset="card" title="Report">
            <n-spin v-if="reportData == undefined" :size="60" style="width: 100%"></n-spin>
            <n-flex v-else>
                <pre style="font-size: larger;">{{ reportData.content }}</pre>
            </n-flex>
        </n-modal>

        <n-drawer v-model:show="showLog" :width="600" placement="right" v-if="data">
            <n-drawer-content title="Log" :native-scrollbar="false">
                <n-spin v-if="logContent == undefined" :size="60" style="width: 100%"></n-spin>
                <n-log v-else :log="logContent" :rows="40" language="log"></n-log>
            </n-drawer-content>
        </n-drawer>
    </n-flex>
</template>
