<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NPageHeader, NSpace, NText, NBreadcrumb, NCollapseTransition, NDivider, NDrawer, NDrawerContent, NProgress, NBreadcrumbItem, NSwitch, NCollapse, useLoadingBar, NCollapseItem, NLog, NIcon, NLayoutContent, NAvatar, NStatistic, NTabs, NTabPane, NCard, NButton, useOsTheme, useMessage, NDescriptions, NDescriptionsItem, NSpin } from 'naive-ui'
import { HomeIcon, RootIcon, TrendIcon, CountIcon, PackageIcon, ReleaseIcon, LogIcon, PreprocessIcon, VersionIcon, DiffIcon, ExtractIcon, EvaluateIcon, ReportIcon } from '../../components/icons'
import { useRouter, useRoute } from 'vue-router'
import HomeBreadcrumbItem from '../../components/breadcrumbs/HomeBreadcrumbItem.vue'
import ReleaseBreadcrumbItem from '../../components/breadcrumbs/ReleaseBreadcrumbItem.vue'
import { useStore } from '../../services/store'
import { Distribution, Release, ApiDescription, ApiDifference, Report, ReleasePair, ProduceMode, ProduceState, PackageProductIndex } from '../../models'
import { numberSum, numberAverage, publicVars } from '../../services/utils'
import { hashedColor } from '../../services/utils'
import NotFound from '../../components/NotFound.vue'
import MetadataViewer from '../../components/metadata/MetadataViewer.vue'
import PackageBreadcrumbItem from '../../components/breadcrumbs/PackageBreadcrumbItem.vue'
import DistributionViewer from '../../components/products/DistributionViewer.vue'
import CountViewer from '../../components/metadata/CountViewer.vue'
import { LineChart } from 'vue-chart-3'
import { BreakingRank, getRankColor, getVerifyColor, VerifyState } from '../../models/difference'
import { AttributeEntry, FunctionEntry, getTypeColor } from '../../models/description'

const store = useStore();
const router = useRouter();
const route = useRoute();
const message = useMessage();
const loadingbar = useLoadingBar();

const params = route.params as {
    id: string,
};

const showStats = ref<boolean>(true);
const showTrends = ref<boolean>(false);

let mode: ProduceMode = parseInt(route.query.mode?.toString() ?? ProduceMode.Access.toString()) as ProduceMode;

const singleDurations = ref();
const pairDurations = ref();
const entryCounts = ref();
const typedEntryCounts = ref();
const rankCounts = ref();
const bcverifyCounts = ref();
const kindCounts = ref();
const locCounts = ref();
const bckindCounts = ref();
const bcCount = ref<number>();
const bcTypeCount = ref<number>();
const bcKwargsCount = ref<number>();
const bcClassCount = ref<number>();
const bcAliasCount = ref<number>();
const avgTotalDuration = ref<number>();
const maxTotalDuration = ref<number>();

const packageName = ref<string>("");
const data = ref<PackageProductIndex>();
const error = ref<boolean>(false);
const showlog = ref<boolean>(false);
const logcontent = ref<string>();

onMounted(async () => {
    loadingbar.start();
    packageName.value = params.id;
    if (packageName.value) {
        try {
            data.value = await store.state.api.package(packageName.value).index();
            publicVars({ "data": data.value });
            mode = ProduceMode.Access;
        }
        catch (e) {
            console.error(e);
            error.value = true;
            message.error(`Failed to load data for ${params.id}.`);
        }
    }
    else {
        error.value = true;
        message.error('Invalid package ID');
    }

    if (error.value) {
        loadingbar.error();
    }
    else {
        loadingbar.finish();
    }
});

async function onLog(value: boolean) {
    if (packageName.value && value) {
        if (logcontent.value == undefined) {
            try {
                logcontent.value = "";
                publicVars({ "log": logcontent.value });
            }
            catch {
                message.error(`Failed to load log for ${params.id}.`);
            }
        }
    }
}

async function onTrends(value: boolean) {
    if (data.value && value && data.value && entryCounts.value == undefined && locCounts.value == undefined && typedEntryCounts.value == undefined && rankCounts.value == undefined && kindCounts.value == undefined && bckindCounts.value == undefined) {
        loadingbar.start();
        try {
            avgTotalDuration.value = 0;
            maxTotalDuration.value = 0;

            let preprocessed = await data.value.loadPreprocessed();
            publicVars({ "preprocessed": preprocessed });
            locCounts.value = getLocCounts(preprocessed);

            let extracted = await data.value.loadExtracted();
            publicVars({ "extracted": extracted });
            entryCounts.value = getEntryCounts(extracted);
            typedEntryCounts.value = getTypedEntryCounts(extracted);

            singleDurations.value = getSingleDurations(data.value.releases, preprocessed, extracted);

            let diffed = await data.value.loadDiffed();
            publicVars({ "diffed": diffed });

            rankCounts.value = getRankCounts(diffed);
            bcverifyCounts.value = getBcverifyCounts(diffed);
            kindCounts.value = getKindCounts(diffed);
            bckindCounts.value = getBreakingKindCounts(diffed);

            let reported = await data.value.loadReported();
            publicVars({ "reported": reported });

            pairDurations.value = getPairDurations(data.value.pairs, diffed, reported);

            loadingbar.finish();
        }
        catch {
            message.error(`Failed to load trends for ${params.id}.`);
            loadingbar.error();
        }
    }
}


function getLocCounts(preprocessed: { [key: string]: Distribution }) {
    let labels = [];
    let rawdata: { [key: string]: number[] } = {};
    let types = ["LOC", "Size"];
    for (let type of types) {
        rawdata[type] = [];
    }
    if (data.value) {
        for (let id of Object.keys(preprocessed)) {
            labels.push(id);
            let pre = preprocessed[id];
            rawdata["LOC"].push(pre.locCount);
            rawdata["Size"].push(pre.fileSize);
        }
    }

    let datasets = [];
    for (let type of types) {
        datasets.push({
            label: `${type} (${numberAverage(rawdata[type]).toFixed(2)})`,
            data: rawdata[type],
            borderColor: hashedColor(type),
            backgroundColor: hashedColor(type),
            tension: 0.1,
            yAxisID: type == "LOC" ? "loc" : "size",
        });
    }
    return {
        labels: labels,
        datasets: datasets,
    };
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

    avgTotalDuration.value = (avgTotalDuration.value ?? 0) + types.map(type => numberAverage(rawdata[type])).reduce((a, b) => a + b, 0) * 2;
    maxTotalDuration.value = (maxTotalDuration.value ?? 0) + types.map(type => Math.max(...rawdata[type])).reduce((a, b) => a + b, 0) * 2;

    let datasets = [];
    for (let type of types) {
        datasets.push({
            label: `${type} (${numberAverage(rawdata[type]).toFixed(2)})`,
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

function getPairDurations(pairs: ReleasePair[], diffed: { [key: string]: ApiDifference }, reported: { [key: string]: Report }) {
    let labels = [];
    let rawdata: { [key: string]: number[] } = {};
    let types = ["Diff", "Report"];
    for (let type of types) {
        rawdata[type] = [];
    }
    if (data.value) {
        for (let item of pairs) {
            let id = item.toString();
            labels.push(id);
            let diff = diffed[id];
            if (diff == undefined) {
                rawdata["Diff"].push(0);
            }
            else {
                rawdata["Diff"].push(diff.duration);
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

    avgTotalDuration.value = (avgTotalDuration.value ?? 0) + types.map(type => numberAverage(rawdata[type])).reduce((a, b) => a + b, 0);
    maxTotalDuration.value = (maxTotalDuration.value ?? 0) + types.map(type => Math.max(...rawdata[type])).reduce((a, b) => a + b, 0);

    let datasets = [];
    for (let type of types) {
        datasets.push({
            label: `${type} (${numberAverage(rawdata[type]).toFixed(2)} s)`,
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
            label: `${type} (${numberAverage(rawdata[type]).toFixed(2)}, ${numberSum(rawdata[type])})`,
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


function getTypedEntryCounts(extracted: { [key: string]: ApiDescription }) {
    let labels = [];
    let rawdata: { [key: string]: number[] } = {};
    let types = ["Typed Function", "Typed Attribute", "Untyped Function", "Untyped Attribute"];
    let colors = ['#18a058', '#d03050', '#18a05880', '#d0305080'];
    for (let type of types) {
        rawdata[type] = [];
    }
    if (data.value) {
        for (let item of data.value.extracted) {
            let id = item.toString();
            labels.push(id)
            let result = extracted[id];
            if (result == undefined) {
                rawdata["Typed Function"].push(0);
                rawdata["Typed Attribute"].push(0);
                rawdata["Untyped Function"].push(0);
                rawdata["Untyped Attribute"].push(0);
            }
            else {
                let entries = Object.values(result.typedEntries());
                rawdata["Typed Function"].push(entries.filter(x => x instanceof FunctionEntry).length);
                rawdata["Typed Attribute"].push(entries.filter(x => x instanceof AttributeEntry).length);
                rawdata["Untyped Function"].push(Object.keys(result.funcs()).length - entries.filter(x => x instanceof FunctionEntry).length);
                rawdata["Untyped Attribute"].push(Object.keys(result.attrs()).length - entries.filter(x => x instanceof AttributeEntry).length);
            }
        }
    }
    let datasets = [];
    for (let type of types) {
        datasets.push({
            label: `${type} (${numberAverage(rawdata[type]).toFixed(2)}, ${numberSum(rawdata[type])})`,
            data: rawdata[type],
            borderColor: colors[types.indexOf(type)],
            backgroundColor: colors[types.indexOf(type)],
            tension: 0.1,
            fill: true,
        });
    }
    return {
        labels: labels,
        datasets: datasets,
    };
}

function getRankCounts(diffed: { [key: string]: ApiDifference }) {
    let labels = [];
    let rawdata: { [key: string]: number[] } = {};
    let ranks = [BreakingRank.Unknown, BreakingRank.Compatible, BreakingRank.Low, BreakingRank.Medium, BreakingRank.High];
    for (let rank of ranks) {
        rawdata[BreakingRank[rank]] = [];
    }
    if (data.value) {
        for (let item of data.value.diffed) {
            let id = item.toString();
            labels.push(id);
            for (let rank of ranks) {
                let result = diffed[id];
                if (result == undefined) {
                    rawdata[BreakingRank[rank]].push(0);
                }
                else {
                    rawdata[BreakingRank[rank]].push(result.rank(rank).length);
                }
            }
        }
    }
    let datasets = [];
    for (let rank of ranks) {
        datasets.push({
            label: `${BreakingRank[rank]} (${numberAverage(rawdata[BreakingRank[rank]]).toFixed(2)}, ${numberSum(rawdata[BreakingRank[rank]])})`,
            data: rawdata[BreakingRank[rank]],
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

function getBcverifyCounts(diffed: { [key: string]: ApiDifference }) {
    let labels = [];
    let rawdata: { [key: string]: number[] } = {};
    let ranks = [VerifyState.Unknown, VerifyState.Fail, VerifyState.Pass];
    for (let rank of ranks) {
        rawdata[VerifyState[rank]] = [];
    }
    if (data.value) {
        for (let item of data.value.diffed) {
            let id = item.toString();
            labels.push(id);
            for (let rank of ranks) {
                let result = diffed[id];
                if (result == undefined) {
                    rawdata[VerifyState[rank]].push(0);
                }
                else {
                    rawdata[VerifyState[rank]].push(result.verify(rank).filter(x => x.rank >= BreakingRank.Low).length);
                }
            }
        }
    }
    let datasets = [];
    for (let rank of ranks) {
        datasets.push({
            label: `${VerifyState[rank]} (${numberAverage(rawdata[VerifyState[rank]]).toFixed(2)}, ${numberSum(rawdata[VerifyState[rank]])})`,
            data: rawdata[VerifyState[rank]],
            borderColor: getVerifyColor(rank),
            backgroundColor: getVerifyColor(rank),
            tension: 0.1,
            fill: true,
        });
    }
    return {
        labels: labels,
        datasets: datasets,
    };
}


function getKindCounts(diffed: { [key: string]: ApiDifference }) {
    let kinds = new Set<string>();
    let labels = [];
    let rawdata: { [key: string]: number[] } = {};

    if (data.value) {
        for (let item in diffed) {
            let val = diffed[item];
            for (let kind of val.kinds()) {
                kinds.add(kind);
            }
        }
        for (let kind of kinds) {
            rawdata[kind] = [];
        }
        for (let item of data.value.diffed) {
            let id = item.toString();
            labels.push(id);
            for (let kind of kinds) {
                let result = diffed[id];
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
            label: `${kind} (${numberAverage(rawdata[kind]).toFixed(2)}, ${numberSum(rawdata[kind])})`,
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


function getBreakingKindCounts(diffed: { [key: string]: ApiDifference }) {
    let kinds = new Set<string>();
    let labels = [];
    let rawdata: { [key: string]: number[] } = {};

    if (data.value) {
        for (let item in diffed) {
            let val = diffed[item];
            for (let kind of val.kinds()) {
                kinds.add(kind);
            }
        }
        for (let kind of kinds) {
            rawdata[kind] = [];
        }
        for (let item of data.value.diffed) {
            let id = item.toString();
            labels.push(id);
            for (let kind of kinds) {
                let result = diffed[id];
                if (result == undefined) {
                    rawdata[kind].push(0);
                }
                else {
                    let count = result.kind(kind).filter((value) => value.rank >= BreakingRank.Low).length;
                    rawdata[kind].push(count);
                }
            }
        }
    }
    let datasets = [];
    bcCount.value = 0;
    bcTypeCount.value = 0;
    bcKwargsCount.value = 0;
    bcClassCount.value = 0;
    bcAliasCount.value = 0;

    for (let kind of kinds) {
        if (numberSum(rawdata[kind]) == 0) {
            continue;
        }
        bcCount.value += numberSum(rawdata[kind]);
        if (kind.indexOf("Alias") != -1) {
            bcAliasCount.value += numberSum(rawdata[kind]);
        }
        if (kind.indexOf("BaseClass") != -1 || kind.indexOf("MethodResolutionOrder") != -1) {
            bcClassCount.value += numberSum(rawdata[kind]);
        }
        if (kind.indexOf("Type") != -1) {
            bcTypeCount.value += numberSum(rawdata[kind]);
        }
        if (kind.indexOf("Candidate") != -1) {
            bcKwargsCount.value += numberSum(rawdata[kind]);
        }
        datasets.push({
            label: `${kind} (${numberAverage(rawdata[kind]).toFixed(2)}, ${numberSum(rawdata[kind])})`,
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
        <n-page-header :title="packageName?.toString() ?? 'Unknown'" subtitle="Packages" @back="() => router.back()">
            <template #avatar>
                <n-avatar>
                    <n-icon>
                        <PackageIcon />
                    </n-icon>
                </n-avatar>
            </template>
            <template #header>
                <n-breadcrumb>
                    <HomeBreadcrumbItem />
                    <PackageBreadcrumbItem />
                    <n-breadcrumb-item>
                        <n-space>
                            <n-icon>
                                <ReleaseIcon />
                            </n-icon>
                            {{ packageName?.toString() ?? "Unknown" }}
                        </n-space>
                    </n-breadcrumb-item>
                </n-breadcrumb>
            </template>
            <template #footer>
                <n-space v-if="data">
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
                    <PipelineLinker />
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

                        <CountViewer :value="data.preprocessed.length" label="Preprocessed" :total="data.releases.length" />
                        <CountViewer :value="data.extracted.length" label="Extracted" :total="data.preprocessed.length" />
                        <CountViewer :value="data.diffed.length" label="Diffed" :total="data.pairs.length" />
                        <CountViewer :value="data.reported.length" label="Reported" :total="data.diffed.length" />
                        <n-statistic label="Average Duration" :value="avgTotalDuration.toFixed(2)" v-if="avgTotalDuration">
                            <template #suffix>
                                <n-text>s</n-text>
                            </template>
                        </n-statistic>
                        <n-statistic label="Maximum Duration" :value="maxTotalDuration.toFixed(2)" v-if="maxTotalDuration">
                            <template #suffix>
                                <n-text>s</n-text>
                            </template>
                        </n-statistic>
                        <CountViewer :value="bcTypeCount" :total="bcCount" label="Type Breaking" v-if="bcTypeCount">
                        </CountViewer>
                        <CountViewer :value="bcKwargsCount" :total="bcCount" label="Kwargs Breaking" v-if="bcKwargsCount">
                        </CountViewer>
                        <CountViewer :value="bcClassCount" :total="bcCount" label="Base Class Breaking" v-if="bcClassCount">
                        </CountViewer>
                        <CountViewer :value="bcAliasCount" :total="bcCount" label="Alias Breaking" v-if="bcAliasCount">
                        </CountViewer>
                    </n-space>
                </n-space>
            </n-collapse-transition>
            <n-collapse-transition :show="showTrends">
                <n-divider>Trends</n-divider>
                <n-space vertical>
                    <LineChart :chart-data="singleDurations"
                        :options="{ plugins: { legend: { position: 'bottom' }, title: { display: true, text: 'Single Processing' } }, scales: { y: { stacked: true } } }"
                        v-if="data.releases.length > 0 && singleDurations"></LineChart>
                    <LineChart :chart-data="pairDurations"
                        :options="{ plugins: { legend: { position: 'bottom' }, title: { display: true, text: 'Pair Processing' } }, scales: { y: { stacked: true } } }"
                        v-if="data.pairs.length > 0 && pairDurations"></LineChart>
                    <LineChart :chart-data="locCounts" :options="{
                        plugins: { legend: { position: 'bottom' }, title: { display: true, text: 'Code Measurements' } }, scales: {
                            loc: {
                                type: 'linear',
                                display: true,
                                position: 'left',
                            },
                            size: {
                                type: 'linear',
                                display: true,
                                position: 'right',
                            },
                        }
                    }" v-if="data.preprocessed.length > 0 && locCounts"></LineChart>
                    <LineChart :chart-data="entryCounts"
                        :options="{ plugins: { legend: { position: 'bottom' }, title: { display: true, text: 'Entries' } }, scales: { y: { stacked: true } } }"
                        v-if="data.extracted.length > 0 && entryCounts"></LineChart>
                    <LineChart :chart-data="typedEntryCounts"
                        :options="{ plugins: { legend: { position: 'bottom' }, title: { display: true, text: 'Typed Entries' } }, scales: { y: { stacked: true } } }"
                        v-if="data.extracted.length > 0 && typedEntryCounts"></LineChart>
                    <LineChart :chart-data="rankCounts"
                        :options="{ plugins: { legend: { position: 'bottom' }, title: { display: true, text: 'Ranks' } }, scales: { y: { stacked: true } } }"
                        v-if="data.diffed.length > 0 && rankCounts"></LineChart>
                    <LineChart :chart-data="bcverifyCounts"
                        :options="{ plugins: { legend: { position: 'bottom' }, title: { display: true, text: 'Breaking Verified' } }, scales: { y: { stacked: true } } }"
                        v-if="data.diffed.length > 0 && bcverifyCounts"></LineChart>
                    <LineChart :chart-data="bckindCounts"
                        :options="{ plugins: { legend: { position: 'bottom' }, title: { display: true, text: 'Breaking Kinds' } }, scales: { y: { stacked: true } } }"
                        v-if="data.diffed.length > 0 && bckindCounts"></LineChart>
                    <LineChart :chart-data="kindCounts"
                        :options="{ plugins: { legend: { position: 'bottom' }, title: { display: true, text: 'Kinds' } }, scales: { y: { stacked: true } } }"
                        v-if="data.diffed.length > 0 && kindCounts"></LineChart>
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
                        <n-button v-for="item in data.releases" :key="item.toString()" text tag="a"
                            :href="`https://pypi.org/project/${item.project}/${item.version}/`" target="_blank">{{
                                item.toString()
                            }}</n-button>
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
                        <n-button v-for="item in data.releases" :key="item.toString()" text tag="a"
                            :href="`/distributions/${item.toString()}`" target="_blank"
                            :type="data.ispreprocessed(item) ? 'success' : 'error'">{{
                                item.toString()
                            }}</n-button>
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
                        <n-button v-for="item in data.preprocessed" :key="item.toString()" text tag="a"
                            :href="`/apis/${item.toString()}`" target="_blank"
                            :type="data.isextracted(item) ? 'success' : 'error'">{{ item.toString() }}</n-button>
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
                        <n-text v-for="item in data.pairs" :key="item.toString()">{{ item.toString() }}</n-text>
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
                        <n-button v-for="item in data.pairs" :key="item.toString()" text tag="a"
                            :href="`/changes/${item.toString()}`" target="_blank"
                            :type="data.isdiffed(item) ? 'success' : 'error'">{{ item.toString() }}</n-button>
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
                        <n-button v-for="item in data.diffed" :key="item.toString()" text tag="a"
                            :href="`/reports/${item.toString()}`" target="_blank"
                            :type="data.isreported(item) ? 'success' : 'error'">{{ item.toString() }}</n-button>
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
