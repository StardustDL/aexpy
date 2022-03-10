<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NPageHeader, NSpace, NText, NBreadcrumb, NCollapseTransition, NDivider, NDrawer, NDrawerContent, NProgress, NBreadcrumbItem, NSwitch, NCollapse, useLoadingBar, NCollapseItem, NLog, NIcon, NLayoutContent, NAvatar, NStatistic, NTabs, NTabPane, NCard, NButton, useOsTheme, useMessage, NDescriptions, NDescriptionsItem, NSpin } from 'naive-ui'
import { HomeIcon, RootIcon, TrendIcon, CountIcon, BatchIcon, ReleaseIcon, LogIcon, PreprocessIcon, VersionIcon, DiffIcon, ExtractIcon, EvaluateIcon, ReportIcon } from '../../components/icons'
import { useRouter, useRoute } from 'vue-router'
import HomeBreadcrumbItem from '../../components/breadcrumbs/HomeBreadcrumbItem.vue'
import ReleaseBreadcrumbItem from '../../components/breadcrumbs/ReleaseBreadcrumbItem.vue'
import { useStore } from '../../services/store'
import { Distribution, Release, ApiDescription, ProjectResult, ProducerOptions, ApiBreaking, ApiDifference, Report, hashedColor, ReleasePair } from '../../models'
import NotFound from '../../components/NotFound.vue'
import MetadataViewer from '../../components/metadata/MetadataViewer.vue'
import BatchBreadcrumbItem from '../../components/breadcrumbs/BatchBreadcrumbItem.vue'
import DistributionViewer from '../../components/products/DistributionViewer.vue'
import CountViewer from '../../components/metadata/CountViewer.vue'
import { LineChart } from 'vue-chart-3'
import { BreakingRank, getRankColor, getRankName } from '../../models/difference'
import { getTypeColor } from '../../models/description'

const store = useStore();
const router = useRouter();
const route = useRoute();
const message = useMessage();
const loadingbar = useLoadingBar();

const params = <{
    provider: string,
    id: string,
}>route.params;

const isIndex = route.query.index == "true";

const showStats = ref<boolean>(true);
const showTrends = ref<boolean>(false);

const query = ProducerOptions.fromQuery(route.query);

const singleDurations = ref();
const pairDurations = ref();
const entryCounts = ref();
const rankCounts = ref();
const kindCounts = ref();

const release = ref<string>("");
const data = ref<ProjectResult>();
const error = ref<boolean>(false);
const showlog = ref<boolean>(false);
const logcontent = ref<string>();

onMounted(async () => {
    loadingbar.start();
    release.value = params.id;
    if (release.value) {
        try {
            if (isIndex) {
                data.value = await store.state.api.batcher.index(release.value, params.provider, query);
            }
            else {
                data.value = await store.state.api.batcher.process(release.value, params.provider, query);
            }
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
        if (logcontent.value == undefined) {
            try {
                if (isIndex) {
                    logcontent.value = await store.state.api.batcher.indexlog(release.value, params.provider, query);
                }
                else {
                    logcontent.value = await store.state.api.batcher.log(release.value, params.provider, query);
                }
            }
            catch {
                message.error(`Failed to load log for ${params.id} by provider ${params.provider}.`);
            }
        }
    }
}

async function onTrends(value: boolean) {
    if (data.value && value && data.value.success && data.value && entryCounts.value == undefined && rankCounts.value == undefined && kindCounts.value == undefined) {
        loadingbar.start();
        let loadOptions = new ProducerOptions(undefined, true, undefined);
        try {
            let preprocessed: { [key: string]: Distribution } = {};
            let extracted: { [key: string]: ApiDescription } = {};
            let diffed: { [key: string]: ApiDifference } = {};
            let evaluated: { [key: string]: ApiBreaking } = {};
            let reported: { [key: string]: Report } = {};
            let promised: Promise<any>[] = [];
            for (let item of data.value.preprocessed) {
                let cur = item;
                let tfunc = async () => {
                    preprocessed[cur.toString()] = await store.state.api.preprocessor.process(cur, params.provider, loadOptions);
                }
                promised.push(tfunc());
            }
            for (let item of data.value.extracted) {
                let cur = item;
                let tfunc = async () => {
                    extracted[cur.toString()] = await store.state.api.extractor.process(cur, params.provider, loadOptions);
                }
                promised.push(tfunc());
            }
            for (let item of data.value.diffed) {
                let cur = item;
                let tfunc = async () => {
                    diffed[cur.toString()] = await store.state.api.differ.process(cur, params.provider, loadOptions);
                }
                promised.push(tfunc());
            }
            for (let item of data.value.evaluated) {
                let cur = item;
                let tfunc = async () => {
                    evaluated[cur.toString()] = await store.state.api.evaluator.process(cur, params.provider, loadOptions);
                }
                promised.push(tfunc());
            }
            for (let item of data.value.reported) {
                let cur = item;
                let tfunc = async () => {
                    reported[cur.toString()] = await store.state.api.reporter.process(cur, params.provider, loadOptions);
                }
                promised.push(tfunc());
            }
            await Promise.all(promised);
            entryCounts.value = getEntryCounts(extracted);
            rankCounts.value = getRankCounts(evaluated);
            kindCounts.value = getKindCounts(evaluated);
            singleDurations.value = getSingleDurations(data.value.releases, preprocessed, extracted);
            pairDurations.value = getPairDurations(data.value.pairs, diffed, evaluated, reported);
            loadingbar.finish();
        }
        catch {
            message.error(`Failed to load trends for ${params.id} by provider ${params.provider}.`);
            loadingbar.error();
        }
    }
}


function getSingleDurations(singles: Release[], preprocessed: { [key: string]: Distribution }, extracted: { [key: string]: ApiDescription }) {
    let labels = [];
    let rawdata: { [key: string]: number[] } = {};
    let types = ["Preprocess", "Extract"];
    for (let type of types) {
        rawdata[type] = [];
    }
    if (data.value) {
        for (let item of singles) {
            let id = item.toString();
            labels.push(id);
            let pre = preprocessed[id];
            if (pre == undefined) {
                rawdata["Preprocess"].push(0);
            }
            else {
                rawdata["Preprocess"].push(pre.duration);
            }
            let ext = extracted[id];
            if (ext == undefined) {
                rawdata["Extract"].push(0);
            }
            else {
                rawdata["Extract"].push(ext.duration);
            }
        }
    }
    let datasets = [];
    for (let type of types) {
        datasets.push({
            label: type,
            data: rawdata[type],
            borderColor: hashedColor(type),
            backgroundColor: hashedColor(type),
            tension: 0.1,
            fill: true,
        });
    }
    return {
        labels: labels,
        datasets: datasets,
    };
}

function getPairDurations(pairs: ReleasePair[], diffed: { [key: string]: ApiDifference }, evaluated: { [key: string]: ApiBreaking }, reported: { [key: string]: Report }) {
    let labels = [];
    let rawdata: { [key: string]: number[] } = {};
    let types = ["Differ", "Evaluate", "Report"];
    for (let type of types) {
        rawdata[type] = [];
    }
    if (data.value) {
        for (let item of pairs) {
            let id = item.toString();
            labels.push(id);
            let diff = diffed[id];
            if (diff == undefined) {
                rawdata["Differ"].push(0);
            }
            else {
                rawdata["Differ"].push(diff.duration);
            }
            let evalu = evaluated[id];
            if (evalu == undefined) {
                rawdata["Evaluate"].push(0);
            }
            else {
                rawdata["Evaluate"].push(evalu.duration);
            }
            let report = reported[id];
            if (report == undefined) {
                rawdata["Report"].push(0);
            }
            else {
                rawdata["Report"].push(report.duration);
            }
        }
    }
    let datasets = [];
    for (let type of types) {
        datasets.push({
            label: type,
            data: rawdata[type],
            borderColor: hashedColor(type),
            backgroundColor: hashedColor(type),
            tension: 0.1,
            fill: true,
        });
    }
    return {
        labels: labels,
        datasets: datasets,
    };
}

function getEntryCounts(extracted: { [key: string]: ApiDescription }) {
    let labels = [];
    let rawdata: { [key: string]: number[] } = {};
    let types = ["Module", "Class", "Function", "Attribute"];
    for (let type of types) {
        rawdata[type] = [];
    }
    if (data.value) {
        for (let item of data.value.extracted) {
            let id = item.toString();
            labels.push(id)
            let result = extracted[id];
            if (result == undefined) {
                rawdata["Module"].push(0);
                rawdata["Class"].push(0);
                rawdata["Function"].push(0);
                rawdata["Attribute"].push(0);
            }
            else {
                rawdata["Module"].push(Object.keys(result.modules()).length);
                rawdata["Class"].push(Object.keys(result.classes()).length);
                rawdata["Function"].push(Object.keys(result.funcs()).length);
                rawdata["Attribute"].push(Object.keys(result.attrs()).length);
            }
        }
    }
    let datasets = [];
    for (let type of types) {
        datasets.push({
            label: type,
            data: rawdata[type],
            borderColor: getTypeColor(type),
            backgroundColor: getTypeColor(type),
            tension: 0.1,
            fill: true,
        });
    }
    return {
        labels: labels,
        datasets: datasets,
    };
}

function getRankCounts(evaluated: { [key: string]: ApiBreaking }) {
    let labels = [];
    let rawdata: { [key: string]: number[] } = {};
    let ranks = [BreakingRank.Unknown, BreakingRank.Compatible, BreakingRank.Low, BreakingRank.Medium, BreakingRank.High];
    for (let rank of ranks) {
        rawdata[getRankName(rank)] = [];
    }
    if (data.value) {
        for (let item of data.value.evaluated) {
            let id = item.toString();
            labels.push(id);
            for (let rank of ranks) {
                let result = evaluated[id];
                if (result == undefined) {
                    rawdata[getRankName(rank)].push(0);
                }
                else {
                    rawdata[getRankName(rank)].push(result.rank(rank).length);
                }
            }
        }
    }
    let datasets = [];
    for (let rank of ranks) {
        datasets.push({
            label: getRankName(rank),
            data: rawdata[getRankName(rank)],
            borderColor: getRankColor(rank),
            backgroundColor: getRankColor(rank),
            tension: 0.1,
            fill: true,
        });
    }
    return {
        labels: labels,
        datasets: datasets,
    };
}


function getKindCounts(evaluated: { [key: string]: ApiBreaking }) {
    let kinds = new Set<string>();
    let labels = [];
    let rawdata: { [key: string]: number[] } = {};

    if (data.value) {
        for (let item of Object.keys(evaluated)) {
            let val = evaluated[item];
            for (let kind of val.kinds()) {
                kinds.add(kind);
            }
        }
        for (let kind of kinds) {
            rawdata[kind] = [];
        }
        for (let item of data.value.evaluated) {
            let id = item.toString();
            labels.push(id);
            for (let kind of kinds) {
                let result = evaluated[id];
                if (result == undefined) {
                    rawdata[kind].push(0);
                }
                else {
                    rawdata[kind].push(result.kind(kind).length);
                }
            }
        }
    }
    let datasets = [];
    for (let kind of kinds) {
        datasets.push({
            label: kind,
            data: rawdata[kind],
            borderColor: hashedColor(kind),
            backgroundColor: hashedColor(kind),
            tension: 0.1,
            fill: true,
        });
    }
    return {
        labels: labels,
        datasets: datasets,
    };
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
                    <n-switch v-model:value="showTrends" @update-value="onTrends">
                        <template #checked>
                            <n-icon size="large">
                                <TrendIcon />
                            </n-icon>
                        </template>
                        <template #unchecked>
                            <n-icon size="large">
                                <TrendIcon />
                            </n-icon>
                        </template>
                    </n-switch>
                </n-space>
            </template>
        </n-page-header>

        <NotFound v-if="error" :path="router.currentRoute.value.fullPath"></NotFound>

        <n-spin v-else-if="!data" :size="80" style="width: 100%"></n-spin>

        <n-space vertical size="large" v-if="data">
            <n-collapse-transition :show="showStats">
                <n-divider>Statistics</n-divider>
                <n-space vertical>
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
                </n-space>
            </n-collapse-transition>
            <n-collapse-transition :show="showTrends">
                <n-divider>Trends</n-divider>
                <n-space vertical>
                    <LineChart
                        :chart-data="singleDurations"
                        :options="{ plugins: { legend: { position: 'right', title: { display: true, text: 'Single Processing' } } }, scales: { y: { stacked: true } } }"
                        v-if="data.releases.length > 0 && singleDurations"
                    ></LineChart>
                    <LineChart
                        :chart-data="pairDurations"
                        :options="{ plugins: { legend: { position: 'right', title: { display: true, text: 'Pair Processing' } } }, scales: { y: { stacked: true } } }"
                        v-if="data.pairs.length > 0 && pairDurations"
                    ></LineChart>
                    <LineChart
                        :chart-data="entryCounts"
                        :options="{ plugins: { legend: { position: 'right', title: { display: true, text: 'Entries' } } }, scales: { y: { stacked: true } } }"
                        v-if="data.extracted.length > 0 && entryCounts"
                    ></LineChart>
                    <LineChart
                        :chart-data="rankCounts"
                        :options="{ plugins: { legend: { position: 'right', title: { display: true, text: 'Ranks' } } }, scales: { y: { stacked: true } } }"
                        v-if="data.evaluated.length > 0 && rankCounts"
                    ></LineChart>
                    <LineChart
                        :chart-data="kindCounts"
                        :options="{ plugins: { legend: { position: 'right', title: { display: true, text: 'Kinds' } } }, scales: { y: { stacked: true } } }"
                        v-if="data.evaluated.length > 0 && kindCounts"
                    ></LineChart>
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
                <n-spin v-if="logcontent == undefined" :size="60" style="width: 100%"></n-spin>
                <n-log v-else :log="logcontent" :rows="40" language="log"></n-log>
            </n-drawer-content>
        </n-drawer>
    </n-space>
</template>
