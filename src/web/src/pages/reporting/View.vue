<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NPageHeader, NSpace, NText, NBreadcrumb, NIcon, NButtonGroup, NLayoutContent, NAvatar, NLog, NSwitch, NStatistic, useLoadingBar, NTabs, NTabPane, NCard, NButton, useOsTheme, useMessage, NDescriptions, NDescriptionsItem, NSpin, NDrawer, NDrawerContent } from 'naive-ui'
import { HomeIcon, RootIcon, PreprocessIcon, ExtractIcon, LogIcon, ReportIcon, EvaluateIcon, DiffIcon } from '../../components/icons'
import { useRouter, useRoute } from 'vue-router'
import HomeBreadcrumbItem from '../../components/breadcrumbs/HomeBreadcrumbItem.vue'
import ReportBreadcrumbItem from '../../components/breadcrumbs/ReportBreadcrumbItem.vue'
import ReleasePairBreadcrumbItem from '../../components/breadcrumbs/ReleasePairBreadcrumbItem.vue'
import { useStore } from '../../services/store'
import { Distribution, ProducerOptions, Release, ReleasePair, Report } from '../../models'
import NotFound from '../../components/NotFound.vue'
import MetadataViewer from '../../components/metadata/MetadataViewer.vue'
import DistributionViewer from '../../components/products/DistributionViewer.vue'
import ProviderLinker from '../../components/metadata/ProviderLinker.vue'
import { publicVars } from '../../services/utils'

const store = useStore();
const router = useRouter();
const route = useRoute();
const message = useMessage();
const loadingbar = useLoadingBar();

const params = <{
    provider: string,
    id: string,
}>route.params;

const query = ProducerOptions.fromQuery(route.query);

const release = ref<ReleasePair>();
const data = ref<Report>();
const error = ref<boolean>(false);
const showlog = ref<boolean>(false);
const logcontent = ref<string>();

const reportContent = ref<string>();

onMounted(async () => {
    loadingbar.start();
    release.value = ReleasePair.fromString(params.id);
    if (release.value) {
        try {
            data.value = await store.state.api.reporter.process(release.value, params.provider, query);
            publicVars({ "data": data.value });
            query.redo = false;
            reportContent.value = await store.state.api.reporter.report(release.value, params.provider, query);
            publicVars({ "report": reportContent.value });
        }
        catch (e) {
            console.error(e);
            error.value = true;
            message.error(`Failed to load preprocessed data for ${params.id} by provider ${params.provider}.`);
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
        if (logcontent.value == undefined) {
            try {
                logcontent.value = await store.state.api.reporter.log(release.value, params.provider, query);
                publicVars({ "log": logcontent.value });
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
            subtitle="Reporting"
            @back="() => router.back()"
        >
            <template #avatar>
                <n-avatar>
                    <n-icon>
                        <ReportIcon />
                    </n-icon>
                </n-avatar>
            </template>
            <template #header>
                <n-breadcrumb>
                    <HomeBreadcrumbItem />
                    <ReportBreadcrumbItem />
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
                            :href="`/evaluating/${params.provider}/${release.toString()}/`"
                            target="_blank"
                            type="info"
                            ghost
                        >
                            <n-icon size="large">
                                <EvaluateIcon />
                            </n-icon>
                        </n-button>
                    </n-button-group>
                    <ProviderLinker />
                </n-space>
            </template>
        </n-page-header>

        <NotFound v-if="error" :path="router.currentRoute.value.fullPath"></NotFound>

        <n-spin v-else-if="!data || reportContent == undefined" :size="80" style="width: 100%"></n-spin>

        <pre v-if="reportContent">{{ reportContent }}</pre>

        <n-drawer v-model:show="showlog" :width="600" placement="right" v-if="data">
            <n-drawer-content title="Log" :native-scrollbar="false">
                <n-spin v-if="logcontent == undefined" :size="60" style="width: 100%"></n-spin>
                <n-log v-else :log="logcontent" :rows="40" language="log"></n-log>
            </n-drawer-content>
        </n-drawer>
    </n-space>
</template>
