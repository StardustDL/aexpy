<script setup lang="ts">
import { ref, computed, onMounted, h } from 'vue'
import { NPageHeader, NSpace, NText, DataTableColumns, NDataTable, NButtonGroup, NBreadcrumb, NPopover, NIcon, NLayoutContent, NAvatar, NLog, NSwitch, NStatistic, NTabs, NTabPane, NCard, NButton, useOsTheme, useMessage, NDescriptions, NDescriptionsItem, NSpin, NDrawer, NDrawerContent } from 'naive-ui'
import { HomeIcon, RootIcon, ReleaseIcon, LogIcon, DiffIcon, ReportIcon, CountIcon, EvaluateIcon } from '../../components/icons'
import { useRouter, useRoute } from 'vue-router'
import HomeBreadcrumbItem from '../../components/breadcrumbs/HomeBreadcrumbItem.vue'
import DiffBreadcrumbItem from '../../components/breadcrumbs/DiffBreadcrumbItem.vue'
import ReleasePairBreadcrumbItem from '../../components/breadcrumbs/ReleasePairBreadcrumbItem.vue'
import { useStore } from '../../services/store'
import { ApiDifference, Distribution, ProducerOptions, Release, ReleasePair, Report } from '../../models'
import NotFound from '../../components/NotFound.vue'
import MetadataViewer from '../../components/metadata/MetadataViewer.vue'
import DistributionViewer from '../../components/products/DistributionViewer.vue'
import PaginationList from '../../components/PaginationList.vue'
import DiffEntryViewer from '../../components/entries/DiffEntryViewer.vue'
import ApiEntryViewer from '../../components/entries/ApiEntryViewer.vue'
import { DiffEntry } from '../../models/difference'
import ApiDifferenceViewer from '../../components/products/ApiDifferenceViewer.vue'

const store = useStore();
const router = useRouter();
const route = useRoute();
const message = useMessage();

const params = <{
    provider: string,
    id: string,
}>route.params;

const showDists = ref<boolean>(false);
const showCounts = ref<boolean>(true);

const query = ProducerOptions.fromQuery(route.query);

const release = ref<ReleasePair>();
const data = ref<ApiDifference>();
const error = ref<boolean>(false);
const showlog = ref<boolean>(false);
const logcontent = ref<string>("");

onMounted(async () => {
    release.value = ReleasePair.fromString(params.id);
    if (release.value) {
        try {
            data.value = await store.state.api.differ.process(release.value, params.provider, query);
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
});

async function onLog(value: boolean) {
    if (release.value && value) {
        if (logcontent.value == "") {
            try {
                logcontent.value = await store.state.api.differ.log(release.value, params.provider, query);
            }
            catch {
                message.error(`Failed to load log for ${params.id} by provider ${params.provider}.`);
            }
        }
    }
}

</script>

<template>
    <n-space vertical :size="20">
        <n-page-header
            :title="release?.toString() ?? 'Unknown'"
            subtitle="Differing"
            @back="() => router.back()"
        >
            <template #avatar>
                <n-avatar>
                    <n-icon>
                        <DiffIcon />
                    </n-icon>
                </n-avatar>
            </template>
            <template #header>
                <n-breadcrumb>
                    <HomeBreadcrumbItem />
                    <DiffBreadcrumbItem />
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
                    <n-switch v-model:value="showCounts">
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
                            :href="`/evaluating/${params.provider}/${release.toString()}/`"
                            target="_blank"
                            type="info"
                            ghost
                        >
                            <n-icon size="large">
                                <EvaluateIcon />
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
            :show-counts="showCounts"
            :show-dists="showDists"
        />

        <n-drawer v-model:show="showlog" :width="600" placement="right" v-if="data">
            <n-drawer-content title="Log" :native-scrollbar="false">
                <n-log :log="logcontent" :rows="40" language="log"></n-log>
            </n-drawer-content>
        </n-drawer>
    </n-space>
</template>
