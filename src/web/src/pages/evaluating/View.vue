<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NPageHeader, NSpace, NText, NBreadcrumb, NButtonGroup, NIcon, NLayoutContent, NAvatar, NLog, NSwitch, NStatistic, useLoadingBar, NTabs, NTabPane, NCard, NButton, useOsTheme, useMessage, NDescriptions, NDescriptionsItem, NSpin, NDrawer, NDrawerContent } from 'naive-ui'
import { HomeIcon, RootIcon, PreprocessIcon, ExtractIcon, CountIcon, ReleaseIcon, LogIcon, EvaluateIcon, ReportIcon, DiffIcon } from '../../components/icons'
import { useRouter, useRoute } from 'vue-router'
import HomeBreadcrumbItem from '../../components/breadcrumbs/HomeBreadcrumbItem.vue'
import EvaluateBreadcrumbItem from '../../components/breadcrumbs/EvaluateBreadcrumbItem.vue'
import ReleasePairBreadcrumbItem from '../../components/breadcrumbs/ReleasePairBreadcrumbItem.vue'
import { useStore } from '../../services/store'
import { ApiBreaking, ApiDifference, Distribution, ProducerOptions, Release, ReleasePair, Report } from '../../models'
import NotFound from '../../components/NotFound.vue'
import MetadataViewer from '../../components/metadata/MetadataViewer.vue'
import DistributionViewer from '../../components/products/DistributionViewer.vue'
import ApiDifferenceViewer from '../../components/products/ApiDifferenceViewer.vue'

const store = useStore();
const router = useRouter();
const route = useRoute();
const message = useMessage();
const loadingbar = useLoadingBar();

const params = <{
    provider: string,
    id: string,
}>route.params;

const showDists = ref<boolean>(false);
const showStats = ref<boolean>(true);

const query = ProducerOptions.fromQuery(route.query);

const release = ref<ReleasePair>();
const data = ref<ApiBreaking>();
const error = ref<boolean>(false);
const showlog = ref<boolean>(false);
const logcontent = ref<string>("");

onMounted(async () => {
    loadingbar.start();
    release.value = ReleasePair.fromString(params.id);
    if (release.value) {
        try {
            data.value = await store.state.api.evaluator.process(release.value, params.provider, query);
            query.redo = false;
        }
        catch {
            error.value = true;
            message.error(`Failed to load data for ${params.id} by provider ${params.provider}.`);
        }
    }
    else {
        error.value = true;
        message.error('Invalid release ID');
    }

    if (error.value) {
        loadingbar.error();
    }
    else {
        loadingbar.finish();
    }
});

async function onLog(value: boolean) {
    if (release.value && value) {
        if (logcontent.value == "") {
            try {
                logcontent.value = await store.state.api.evaluator.log(release.value, params.provider, query);
            }
            catch {
                message.error(`Failed to load log for ${params.id} by provider ${params.provider}.`);
            }
        }
    }
}
</script>

<template>
    <n-space vertical>
        <n-page-header
            :title="release?.toString() ?? 'Unknown'"
            subtitle="Evaluating"
            @back="() => router.back()"
        >
            <template #avatar>
                <n-avatar>
                    <n-icon>
                        <EvaluateIcon />
                    </n-icon>
                </n-avatar>
            </template>
            <template #header>
                <n-breadcrumb>
                    <HomeBreadcrumbItem />
                    <EvaluateBreadcrumbItem />
                    <ReleasePairBreadcrumbItem :release="release" />
                </n-breadcrumb>
            </template>
            <template #footer>
                <n-space v-if="data">
                    <MetadataViewer :data="data" />
                    <n-switch v-model:value="showlog" @update-value="onLog">
                        <template #checked>
                            <n-icon size="large">
                                <LogIcon />
                            </n-icon>
                        </template>
                        <template #unchecked>
                            <n-icon size="large">
                                <LogIcon />
                            </n-icon>
                        </template>
                    </n-switch>
                    <n-switch v-model:value="showDists">
                        <template #checked>
                            <n-icon size="large">
                                <ReleaseIcon />
                            </n-icon>
                        </template>
                        <template #unchecked>
                            <n-icon size="large">
                                <ReleaseIcon />
                            </n-icon>
                        </template>
                    </n-switch>
                    <n-switch v-model:value="showStats">
                        <template #checked>
                            <n-icon size="large">
                                <CountIcon />
                            </n-icon>
                        </template>
                        <template #unchecked>
                            <n-icon size="large">
                                <CountIcon />
                            </n-icon>
                        </template>
                    </n-switch>

                    <n-button-group size="small" v-if="release">
                        <n-button
                            tag="a"
                            :href="`/preprocessing/${params.provider}/${release.old.toString()}/`"
                            target="_blank"
                            type="info"
                            ghost
                        >
                            <n-icon size="large">
                                <PreprocessIcon />
                            </n-icon>
                        </n-button>
                        <n-button
                            tag="a"
                            :href="`/extracting/${params.provider}/${release.old.toString()}/`"
                            target="_blank"
                            type="info"
                            ghost
                        >
                            <n-icon size="large">
                                <ExtractIcon />
                            </n-icon>
                        </n-button>
                        <n-button
                            tag="a"
                            :href="`/preprocessing/${params.provider}/${release.new.toString()}/`"
                            target="_blank"
                            type="info"
                            ghost
                        >
                            <n-icon size="large">
                                <PreprocessIcon />
                            </n-icon>
                        </n-button>
                        <n-button
                            tag="a"
                            :href="`/extracting/${params.provider}/${release.new.toString()}/`"
                            target="_blank"
                            type="info"
                            ghost
                        >
                            <n-icon size="large">
                                <ExtractIcon />
                            </n-icon>
                        </n-button>
                        <n-button
                            tag="a"
                            :href="`/differing/${params.provider}/${release.toString()}/`"
                            target="_blank"
                            type="info"
                            ghost
                        >
                            <n-icon size="large">
                                <DiffIcon />
                            </n-icon>
                        </n-button>
                        <n-button
                            tag="a"
                            :href="`/reporting/${params.provider}/${release.toString()}/`"
                            target="_blank"
                            type="info"
                            ghost
                        >
                            <n-icon size="large">
                                <ReportIcon />
                            </n-icon>
                        </n-button>
                    </n-button-group>
                </n-space>
            </template>
        </n-page-header>

        <NotFound v-if="error" :path="router.currentRoute.value.fullPath"></NotFound>

        <n-spin v-else-if="!data" :size="80" style="width: 100%"></n-spin>

        <ApiDifferenceViewer
            v-if="data"
            :data="data"
            :show-stats="showStats"
            :show-dists="showDists"
        />

        <n-drawer v-model:show="showlog" :width="600" placement="right" v-if="data">
            <n-drawer-content title="Log" :native-scrollbar="false">
                <n-log :log="logcontent" :rows="40" language="log"></n-log>
            </n-drawer-content>
        </n-drawer>
    </n-space>
</template>
