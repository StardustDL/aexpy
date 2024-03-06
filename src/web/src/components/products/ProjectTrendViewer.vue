<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NPageHeader, NFlex, NSpace, NText, useLoadingBar, NStatistic, useMessage, NSpin } from 'naive-ui'
import { Distribution, Release, ApiDescription, ApiDifference, Report, ReleasePair, ProduceState, ProjectProductIndex } from '../../models'
import { numberSum, numberAverage, publicVars, apiUrl, changeUrl, distributionUrl, reportUrl, hashedColor } from '../../services/utils'
import NotFound from '../../components/NotFound.vue'
import CountViewer from '../../components/metadata/CountViewer.vue'
import { LineChart } from 'vue-chart-3'
import { BreakingRank, getRankColor } from '../../models/difference'
import { AttributeEntry, FunctionEntry, getTypeColor } from '../../models/description'

const props = defineProps<{ data: ProjectProductIndex }>();

const message = useMessage();
const loadingbar = useLoadingBar();

const singleDurations = ref();
const pairDurations = ref();
const entryCounts = ref();
const typedEntryCounts = ref();
const rankCounts = ref();
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

const nodata = computed(() => entryCounts.value == undefined
    && locCounts.value == undefined
    && typedEntryCounts.value == undefined
    && rankCounts.value == undefined
    && kindCounts.value == undefined
    && bckindCounts.value == undefined);
const error = ref(false);

async function load() {
    if (nodata.value && !error.value) {
        loadingbar.start();
        try {
            avgTotalDuration.value = 0;
            maxTotalDuration.value = 0;

            let preprocessed = await props.data.loadPreprocessed();
            publicVars({ "preprocessed": preprocessed });
            locCounts.value = getLocCounts(preprocessed);

            let extracted = await props.data.loadExtracted();
            publicVars({ "extracted": extracted });
            entryCounts.value = getEntryCounts(extracted);
            typedEntryCounts.value = getTypedEntryCounts(extracted);

            singleDurations.value = getSingleDurations(preprocessed, extracted);

            let diffed = await props.data.loadDiffed();
            publicVars({ "diffed": diffed });

            rankCounts.value = getRankCounts(diffed);
            kindCounts.value = getKindCounts(diffed);
            bckindCounts.value = getBreakingKindCounts(diffed);

            let reported = await props.data.loadReported();
            publicVars({ "reported": reported });

            pairDurations.value = getPairDurations(diffed, reported);

            loadingbar.finish();
        }
        catch {
            message.error(`Failed to load trends.`);
            loadingbar.error();
            error.value = true;
        }
    }
}

onMounted(() => load());

function getLocCounts(preprocessed: { [key: string]: Distribution }) {
    let labels = [];
    let rawdata: { [key: string]: number[] } = {};
    let types = ["LOC", "Size"];
    for (let type of types) {
        rawdata[type] = [];
    }
    for (let item of props.data.preprocessed) {
        let id = item.toString();
        labels.push(id)
        let result = preprocessed[id];
        if (result == undefined) {
            rawdata["LOC"].push(0);
            rawdata["Size"].push(0);
        }
        else {
            rawdata["LOC"].push(result.locCount);
            rawdata["Size"].push(result.fileSize);
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


function getSingleDurations(preprocessed: { [key: string]: Distribution }, extracted: { [key: string]: ApiDescription }) {
    let labels = [];
    let rawdata: { [key: string]: number[] } = {};
    let types = ["Preprocess", "Extract"];
    for (let type of types) {
        rawdata[type] = [];
    }
    for (let item of props.data.releases) {
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

function getPairDurations(diffed: { [key: string]: ApiDifference }, reported: { [key: string]: Report }) {
    let labels = [];
    let rawdata: { [key: string]: number[] } = {};
    let types = ["Diff", "Report"];
    for (let type of types) {
        rawdata[type] = [];
    }
    for (let item of props.data.pairs) {
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
    for (let item of props.data.extracted) {
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
            rawdata["Module"].push(Object.keys(result.modules).length);
            rawdata["Class"].push(Object.keys(result.classes).length);
            rawdata["Function"].push(Object.keys(result.functions).length);
            rawdata["Attribute"].push(Object.keys(result.attributes).length);
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
    for (let item of props.data.extracted) {
        let id = item.toString();
        labels.push(id);
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
            rawdata["Untyped Function"].push(Object.keys(result.functions).length - entries.filter(x => x instanceof FunctionEntry).length);
            rawdata["Untyped Attribute"].push(Object.keys(result.attributes).length - entries.filter(x => x instanceof AttributeEntry).length);
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
    for (let item of props.data.diffed) {
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

function getKindCounts(diffed: { [key: string]: ApiDifference }) {
    let kinds = new Set<string>();
    let labels = [];
    let rawdata: { [key: string]: number[] } = {};

    for (let item in diffed) {
        let val = diffed[item];
        for (let kind of val.kinds()) {
            kinds.add(kind);
        }
    }
    for (let kind of kinds) {
        rawdata[kind] = [];
    }
    for (let item of props.data.diffed) {
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

    for (let item in diffed) {
        let val = diffed[item];
        for (let kind of val.kinds()) {
            kinds.add(kind);
        }
    }
    for (let kind of kinds) {
        rawdata[kind] = [];
    }
    for (let item of props.data.diffed) {
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
    <NotFound v-if="error" path="/" size="huge"></NotFound>

    <n-spin v-else-if="nodata" :size="160" style="width: 100%; margin: 50px"></n-spin>

    <n-flex v-else vertical>
        <n-flex size="large">
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
        </n-flex>
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
        <LineChart :chart-data="bckindCounts"
            :options="{ plugins: { legend: { position: 'bottom' }, title: { display: true, text: 'Breaking Kinds' } }, scales: { y: { stacked: true } } }"
            v-if="data.diffed.length > 0 && bckindCounts"></LineChart>
        <LineChart :chart-data="kindCounts"
            :options="{ plugins: { legend: { position: 'bottom' }, title: { display: true, text: 'Kinds' } }, scales: { y: { stacked: true } } }"
            v-if="data.diffed.length > 0 && kindCounts"></LineChart>
    </n-flex>
</template>
