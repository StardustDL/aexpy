<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NPageHeader, NSpace, NText, NBreadcrumb, NCollapseTransition, NDivider, NDrawer, NDrawerContent, NProgress, NBreadcrumbItem, NSwitch, NCollapse, useLoadingBar, NCollapseItem, NLog, NIcon, NLayoutContent, NAvatar, NStatistic, NTabs, NTabPane, NCard, NButton, useOsTheme, useMessage, NDescriptions, NDescriptionsItem, NSpin } from 'naive-ui'
import { HomeIcon, RootIcon, CountIcon, BatchIcon, ReleaseIcon, LogIcon, PreprocessIcon, VersionIcon, DiffIcon, ExtractIcon, EvaluateIcon, ReportIcon } from '../../components/icons'
import { useRouter, useRoute } from 'vue-router'
import HomeBreadcrumbItem from '../../components/breadcrumbs/HomeBreadcrumbItem.vue'
import ReleaseBreadcrumbItem from '../../components/breadcrumbs/ReleaseBreadcrumbItem.vue'
import { useStore } from '../../services/store'
import { Distribution, Release, ApiDescription, ProjectResult, ProducerOptions } from '../../models'
import NotFound from '../../components/NotFound.vue'
import MetadataViewer from '../../components/metadata/MetadataViewer.vue'
import BatchBreadcrumbItem from '../../components/breadcrumbs/BatchBreadcrumbItem.vue'
import DistributionViewer from '../../components/products/DistributionViewer.vue'
import CountViewer from '../../components/metadata/CountViewer.vue'

const store = useStore();
const router = useRouter();
const route = useRoute();
const message = useMessage();
const loadingbar = useLoadingBar();

const params = <{
    provider: string,
    id: string,
}>route.params;

const showCounts = ref<boolean>(true);

const query = ProducerOptions.fromQuery(route.query);

const release = ref<string>("");
const data = ref<ProjectResult>();
const error = ref<boolean>(false);
const showlog = ref<boolean>(false);
const logcontent = ref<string>("");

onMounted(async () => {
    loadingbar.start();
    release.value = params.id;
    if (release.value) {
        try {
            data.value = await store.state.api.batcher.index(release.value, params.provider, query);
            query.redo = false;
        }
        catch (e) {
            console.error(e);
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
                logcontent.value = await store.state.api.batcher.indexlog(release.value, params.provider, query);
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
            subtitle="Batching"
            @back="() => router.back()"
        >
            <template #avatar>
                <n-avatar>
                    <n-icon>
                        <BatchIcon />
                    </n-icon>
                </n-avatar>
            </template>
            <template #header>
                <n-breadcrumb>
                    <HomeBreadcrumbItem />
                    <BatchBreadcrumbItem />
                    <n-breadcrumb-item>
                        <n-space>
                            <n-icon>
                                <ReleaseIcon />
                            </n-icon>
                            {{ release?.toString() ?? "Unknown" }}
                        </n-space>
                    </n-breadcrumb-item>
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
                </n-space>
            </template>
        </n-page-header>

        <NotFound v-if="error" :path="router.currentRoute.value.fullPath"></NotFound>

        <n-spin v-else-if="!data" :size="80" style="width: 100%"></n-spin>

        <n-space vertical size="large" v-if="data">
            <n-collapse-transition :show="showCounts">
                <n-divider>Counts</n-divider>
                <n-space>
                    <CountViewer :value="data.releases.length" label="Releases"></CountViewer>
                    <CountViewer :value="data.pairs.length" label="Pairs"></CountViewer>
                    <n-divider vertical />

                    <CountViewer
                        :value="data.preprocessed.length"
                        label="Preprocessed"
                        :total="data.releases.length"
                    />
                    <CountViewer
                        :value="data.extracted.length"
                        label="Extracted"
                        :total="data.preprocessed.length"
                    />
                    <CountViewer
                        :value="data.diffed.length"
                        label="Diffed"
                        :total="data.pairs.length"
                    />
                    <CountViewer
                        :value="data.evaluated.length"
                        label="Evaluated"
                        :total="data.pairs.length"
                    />
                    <CountViewer
                        :value="data.reported.length"
                        label="Reported"
                        :total="data.evaluated.length"
                    />
                </n-space>
            </n-collapse-transition>
            <n-divider>Data</n-divider>
            <n-collapse>
                <n-collapse-item name="releases">
                    <template #header>
                        <n-space>
                            <n-icon size="large">
                                <ReleaseIcon />
                            </n-icon>Releases
                        </n-space>
                    </template>
                    <n-space>
                        <span
                            v-for="item in data.releases"
                            :key="item.toString()"
                        >{{ item.toString() }}</span>
                    </n-space>
                </n-collapse-item>
                <n-collapse-item title="Preprocessed" name="preprocessed">
                    <template #header>
                        <n-space>
                            <n-icon size="large">
                                <PreprocessIcon />
                            </n-icon>Preprocessed
                        </n-space>
                    </template>
                    <n-space>
                        <n-button
                            v-for="item in data.releases"
                            :key="item.toString()"
                            text
                            tag="a"
                            :href="`/preprocessing/${params.provider}/${item.toString()}/?onlyCache=true`"
                            target="_blank"
                            :type="data.ispreprocessed(item) ? 'success' : 'error'"
                        >{{ item.toString() }}</n-button>
                    </n-space>
                </n-collapse-item>
                <n-collapse-item name="extracted">
                    <template #header>
                        <n-space>
                            <n-icon size="large">
                                <ExtractIcon />
                            </n-icon>Extracted
                        </n-space>
                    </template>
                    <n-space>
                        <n-button
                            v-for="item in data.preprocessed"
                            :key="item.toString()"
                            text
                            tag="a"
                            :href="`/extracting/${params.provider}/${item.toString()}/?onlyCache=true`"
                            target="_blank"
                            :type="data.isextracted(item) ? 'success' : 'error'"
                        >{{ item.toString() }}</n-button>
                    </n-space>
                </n-collapse-item>
                <n-collapse-item name="pairs">
                    <template #header>
                        <n-space>
                            <n-icon size="large">
                                <VersionIcon />
                            </n-icon>Pairs
                        </n-space>
                    </template>
                    <n-space>
                        <span
                            v-for="item in data.pairs"
                            :key="item.toString()"
                        >{{ item.toString() }}</span>
                    </n-space>
                </n-collapse-item>
                <n-collapse-item name="diffed">
                    <template #header>
                        <n-space>
                            <n-icon size="large">
                                <DiffIcon />
                            </n-icon>Diffed
                        </n-space>
                    </template>
                    <n-space>
                        <n-button
                            v-for="item in data.pairs"
                            :key="item.toString()"
                            text
                            tag="a"
                            :href="`/differing/${params.provider}/${item.toString()}/?onlyCache=true`"
                            target="_blank"
                            :type="data.isdiffed(item) ? 'success' : 'error'"
                        >{{ item.toString() }}</n-button>
                    </n-space>
                </n-collapse-item>
                <n-collapse-item name="evaluated">
                    <template #header>
                        <n-space>
                            <n-icon size="large">
                                <EvaluateIcon />
                            </n-icon>Evaluated
                        </n-space>
                    </template>
                    <n-space>
                        <n-button
                            v-for="item in data.diffed"
                            :key="item.toString()"
                            text
                            tag="a"
                            :href="`/evaluating/${params.provider}/${item.toString()}/?onlyCache=true`"
                            target="_blank"
                            :type="data.isevaluated(item) ? 'success' : 'error'"
                        >{{ item.toString() }}</n-button>
                    </n-space>
                </n-collapse-item>
                <n-collapse-item name="reported">
                    <template #header>
                        <n-space>
                            <n-icon size="large">
                                <ReportIcon />
                            </n-icon>Reported
                        </n-space>
                    </template>
                    <n-space>
                        <n-button
                            v-for="item in data.evaluated"
                            :key="item.toString()"
                            text
                            tag="a"
                            :href="`/reporting/${params.provider}/${item.toString()}/?onlyCache=true`"
                            target="_blank"
                            :type="data.isreported(item) ? 'success' : 'error'"
                        >{{ item.toString() }}</n-button>
                    </n-space>
                </n-collapse-item>
            </n-collapse>
        </n-space>

        <n-drawer v-model:show="showlog" :width="600" placement="right" v-if="data">
            <n-drawer-content title="Log" :native-scrollbar="false">
                <n-log :log="logcontent" :rows="40" language="log"></n-log>
            </n-drawer-content>
        </n-drawer>
    </n-space>
</template>
