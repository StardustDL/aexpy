<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NPageHeader, NFlex, NTooltip, NDivider, NCollapseTransition, NLayout, NText, NBreadcrumb, NIcon, NButtonGroup, NLayoutContent, NAvatar, NLog, NSwitch, NStatistic, useLoadingBar, NTabs, NTabPane, NCard, NButton, useOsTheme, useMessage, NDescriptions, NDescriptionsItem, NSpin, NDrawer, NDrawerContent } from 'naive-ui'
import { HomeIcon, RootIcon, DistributionIcon, DescriptionIcon, LogIcon, ReportIcon, EvaluateIcon, DifferenceIcon } from '../../components/icons'
import { useRouter } from 'vue-router'
import HomeBreadcrumbItem from '../../components/breadcrumbs/HomeBreadcrumbItem.vue'
import ProjectBreadcrumbItem from '../../components/breadcrumbs/ProjectBreadcrumbItem.vue'
import ReleasePairBreadcrumbItem from '../../components/breadcrumbs/ReleasePairBreadcrumbItem.vue'
import { useStore } from '../../services/store'
import { Distribution, Release, ReleasePair, Report } from '../../models'
import NotFound from '../../components/NotFound.vue'
import MetadataViewer from '../../components/metadata/MetadataViewer.vue'
import DistributionViewer from '../../components/products/DistributionViewer.vue'
import { publicVars } from '../../services/utils'
import DistributionSwitch from '../../components/switches/DistributionSwitch.vue'
import LogSwitchPanel from '../../components/switches/LogSwitchPanel.vue'
import DistributionLink from '../../components/links/DistributionLink.vue'
import DescriptionLink from '../../components/links/DescriptionLink.vue'
import DifferenceLink from '../../components/links/DifferenceLink.vue'

const store = useStore();
const router = useRouter();
const message = useMessage();
const loadingbar = useLoadingBar();

const props = defineProps<{
    project: string,
    old: string,
    new: string,
}>();
const release = new ReleasePair(new Release(props.project, props.old), new Release(props.project, props.new));

const data = ref<Report>();
const error = ref<boolean>(false);
const showDists = ref<boolean>(false);

onMounted(async () => {
    loadingbar.start();
    try {
        data.value = await store.state.api.report(release);
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
</script>

<template>
    <n-flex vertical>
        <n-page-header :title="release?.toString() ?? 'Unknown'" subtitle="Report" @back="() => router.back()">
            <template #avatar>
                <n-avatar>
                    <n-icon :component="ReportIcon" />
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
                <n-flex v-if="data" :align="'center'">
                    <MetadataViewer :data="data" />
                    <n-button-group size="small" v-if="release">
                        <DistributionLink :release="release.old" />
                        <DescriptionLink :release="release.old" />
                        <DistributionLink :release="release.new" />
                        <DescriptionLink :release="release.new" />
                        <DifferenceLink :pair="release" />
                    </n-button-group>
                    <DistributionSwitch v-model="showDists" />
                    <LogSwitchPanel :load="() => store.state.api.reportLog(release)" />
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
                        Distributions
                    </n-flex>
                </n-divider>
                <n-flex>
                    <DistributionViewer v-if="data.old" :data="data.old" />
                    <DistributionViewer v-if="data.new" :data="data.new" />
                </n-flex>
            </n-collapse-transition>
        </n-flex>

        <n-flex v-if="data">
            <pre style="font-size: larger;">{{ data.content }}</pre>
        </n-flex>
    </n-flex>
</template>
