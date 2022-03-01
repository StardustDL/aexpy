<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NPageHeader, NSpace, NText, NBreadcrumb, NIcon, NLayoutContent, NAvatar, NLog, NSwitch, NStatistic, NTabs, NTabPane, NCard, NButton, useOsTheme, useMessage, NDescriptions, NDescriptionsItem, NSpin, NDrawer, NDrawerContent } from 'naive-ui'
import { HomeIcon, RootIcon, LogIcon, ReportIcon } from '../../components/icons'
import { useRouter, useRoute } from 'vue-router'
import HomeBreadcrumbItem from '../../components/breadcrumbs/HomeBreadcrumbItem.vue'
import DiffBreadcrumbItem from '../../components/breadcrumbs/DiffBreadcrumbItem.vue'
import ReleasePairBreadcrumbItem from '../../components/breadcrumbs/ReleasePairBreadcrumbItem.vue'
import { useStore } from '../../services/store'
import { ApiBreaking, ApiDifference, Distribution, ProducerOptions, Release, ReleasePair, Report } from '../../models'
import NotFound from '../../components/NotFound.vue'
import MetadataViewer from '../../components/metadata/MetadataViewer.vue'
import DistributionViewer from '../../components/metadata/DistributionViewer.vue'

const store = useStore();
const router = useRouter();
const route = useRoute();
const message = useMessage();

const params = <{
    provider: string,
    id: string,
}>route.params;

const query = ProducerOptions.fromQuery(route.query);

const release = ref<ReleasePair>();
const data = ref<ApiBreaking>();
const error = ref<boolean>(false);
const showlog = ref<boolean>(false);
const logcontent = ref<string>("");

onMounted(async () => {
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
                        <ReportIcon />
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
                            </n-icon>Show Log
                        </template>
                        <template #unchecked>
                            <n-icon size="large">
                                <LogIcon />
                            </n-icon>Hide Log
                        </template>
                    </n-switch>
                </n-space>
            </template>
        </n-page-header>

        <NotFound v-if="error" :path="router.currentRoute.value.fullPath"></NotFound>

        <n-spin v-else-if="!data" :size="80" style="width: 100%"></n-spin>

        <n-space vertical size="large">
            <DistributionViewer v-if="data?.old" :data="data.old" title="Old Distribution"/>

            <DistributionViewer v-if="data?.new" :data="data.new" title="New Distribution"/>

            <n-descriptions title="Differences" v-if="data">
                <n-descriptions-item>
                    <template #label>Entries</template>
                    {{ Object.keys(data.entries).length }}
                </n-descriptions-item>
            </n-descriptions>
        </n-space>

        <n-drawer v-model:show="showlog" :width="600" placement="right" v-if="data">
            <n-drawer-content title="Log" :native-scrollbar="false">
                <n-log :log="logcontent" :rows="50" language="log"></n-log>
            </n-drawer-content>
        </n-drawer>
    </n-space>
</template>
