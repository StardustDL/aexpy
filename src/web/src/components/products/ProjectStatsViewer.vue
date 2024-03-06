<script setup lang="ts">
import { ref, computed, onMounted, Ref } from 'vue'
import { NPageHeader, NFlex, NSpace, NText, useLoadingBar, NTab, NTabs, NStatistic, useMessage, NSpin } from 'naive-ui'
import { Distribution, Release, ApiDescription, ApiDifference, Report, ReleasePair, ProduceState, PackageProductIndex, PackageStats } from '../../models'
import { numberSum, numberAverage, publicVars, apiUrl, changeUrl, distributionUrl, reportUrl, hashedColor } from '../../services/utils'
import NotFound from '../../components/NotFound.vue'
import CountViewer from '../../components/metadata/CountViewer.vue'
import { LineChart } from 'vue-chart-3'
import { BreakingRank, getRankColor } from '../../models/difference'
import { AttributeEntry, FunctionEntry, getTypeColor } from '../../models/description'

const props = defineProps<{ data: PackageProductIndex }>();
const distributionStats = ref<PackageStats>();
const apiStats = ref<PackageStats>();
const changeStats = ref<PackageStats>();
const reportStats = ref<PackageStats>();

const message = useMessage();
const loadingbar = useLoadingBar();

type StatType = { [key: string]: { [key: string]: number } };

function combineStats(a: StatType, b: StatType) {
    let res: StatType = {};
    for (let id in a) {
        res[id] = a[id];
    }
    for (let id in b) {
        if (!(id in res))
            res[id] = b[id];
        else res[id] = { ...res[id], ...b[id] };
    }
    return res;
}

const singleDurations = computed(() => {
    let data: StatType = {};
    if (distributionStats.value) {
        data = combineStats(data, distributionStats.value.selectMany<number>(["duration", "preprocess"]));
    }
    if (apiStats.value) {
        data = combineStats(data, apiStats.value.selectMany<number>(["duration", "extract"]));
    }
    return buildLineChartSingle(data, props.data.releases.map(x => x.toString()), (t) => {
        return { fill: true };
    });
});
const pairDurations = computed(() => {
    let data: StatType = {};
    if (changeStats.value) {
        data = combineStats(data, changeStats.value.selectMany<number>(["duration", "diff"]));
    }
    if (reportStats.value) {
        data = combineStats(data, reportStats.value.selectMany<number>(["duration", "report"]));
    }
    return buildLineChartSingle(data, props.data.pairs.map(x => x.toString()), (t) => {
        return { fill: true };
    });
});
const locCounts = computed(() => {
    if (distributionStats.value) {
        let data: StatType = distributionStats.value.selectMany<number>("loc", ["filesize", "size"]);
        return buildLineChartSingle(data, props.data.preprocessed.map(x => x.toString()), (t) => {
            return { yAxisID: t }
        });
    }
});
const entryCounts = computed(() => {
    if (apiStats.value) {
        let data: StatType = apiStats.value.selectMany<number>(
            ["modules", "Module"], ["classes", "Class"], ["functions", "Function"], ["attributes", "Attribute"]);
        return buildLineChartSingle(data, props.data.preprocessed.map(x => x.toString()), (t) => {
            return {
                fill: true,
                borderColor: getTypeColor(t),
                backgroundColor: getTypeColor(t),
            }
        });
    }
});
const typedEntryCounts = computed(() => {
    if (apiStats.value) {
        let data: StatType = apiStats.value.selectMany<number>(
            ["typed_functions", "Typed Function"], ["typed_attributes", "Typed Attribute"],
            ["untyped_functions", "Untyped Function"], ["untyped_attributes", "Untyped Attribute"],
            ["typed_parameters", "Typed Parameters"], ["untyped_parameters", "Untyped Parameters"]);
        return buildLineChartSingle(data, props.data.preprocessed.map(x => x.toString()), (t) => {
            let parts = t.split(" ");
            if (parts[1] == "Parameters") {
                return {}
            } else {
                return {
                    fill: true,
                    borderColor: getTypeColor(parts[1]) + (parts[0] == "Untyped" ? "80" : ""),
                    backgroundColor: getTypeColor(parts[1]) + (parts[0] == "Untyped" ? "80" : ""),
                }
            }
        });
    }
});
const rankCounts = computed(() => {
    if (changeStats.value) {
        let data: StatType = changeStats.value.select("ranks");
        return buildLineChartSingle(data, props.data.diffed.map(x => x.toString()), (t) => {
            return {
                fill: true,
                borderColor: getRankColor(BreakingRank[t as keyof typeof BreakingRank]),
                backgroundColor: getRankColor(BreakingRank[t as keyof typeof BreakingRank]),
            }
        });
    }
});
const kindCounts = computed(() => {
    if (changeStats.value) {
        let data: StatType = changeStats.value.select("kinds");
        return buildLineChartSingle(data, props.data.diffed.map(x => x.toString()), (t) => {
            return {
                fill: true,
            }
        });
    }
});
const bckindCounts = computed(() => {
    if (changeStats.value) {
        let data: StatType = changeStats.value.select("breaking_kinds");
        return buildLineChartSingle(data, props.data.diffed.map(x => x.toString()), (t) => {
            return {
                fill: true,
            }
        });
    }
});
const bcCount = computed(() => {
    if (changeStats.value) {
        return numberSum(Object.values(changeStats.value.select<number>("breaking")));
    }
    return 0;
});
const bcTypeCount = computed(() => {
    let result = 0;
    if (changeStats.value) {
        let data: StatType = changeStats.value.select("breaking_kinds");
        for (let value of Object.values(data)) {
            for (let kind in value) {
                if (kind.includes("Type")) {
                    result += value[kind];
                }
            }
        }
    }
    return result;
});
const bcKwargsCount = computed(() => {
    let result = 0;
    if (changeStats.value) {
        let data: StatType = changeStats.value.select("breaking_kinds");
        for (let value of Object.values(data)) {
            for (let kind in value) {
                if (kind.includes("Candidate")) {
                    result += value[kind];
                }
            }
        }
    }
    return result;
});
const bcClassCount = computed(() => {
    let result = 0;
    if (changeStats.value) {
        let data: StatType = changeStats.value.select("breaking_kinds");
        for (let value of Object.values(data)) {
            for (let kind in value) {
                if (kind.includes("BaseClass") || kind.includes("MethodResolutionOrder")) {
                    result += value[kind];
                }
            }
        }
    }
    return result;
});
const bcAliasCount = computed(() => {
    let result = 0;
    if (changeStats.value) {
        let data: StatType = changeStats.value.select("breaking_kinds");
        for (let value of Object.values(data)) {
            for (let kind in value) {
                if (kind.includes("Alias")) {
                    result += value[kind];
                }
            }
        }
    }
    return result;
});

const avgTotalDuration = computed(() => {
    let calc = (raw: Ref<PackageStats | undefined>) => {
        if (raw.value) {
            let values = Object.values(raw.value.select<number>("duration"));
            if (values.length > 0) {
                return numberAverage(values);
            }
        }
        return 0.0;
    }
    return (calc(distributionStats) + calc(apiStats)) * 2 + calc(changeStats) + calc(reportStats);
});
const maxTotalDuration = computed(() => {
    let calc = (raw: Ref<PackageStats | undefined>) => {
        if (raw.value) {
            let values = Object.values(raw.value.select<number>("duration"));
            if (values.length > 0) {
                return Math.max(...values);
            }
        }
        return 0.0;
    }
    return (calc(distributionStats) + calc(apiStats)) * 2 + calc(changeStats) + calc(reportStats);
});

const nodata = computed(() => distributionStats.value == undefined
    || apiStats.value == undefined
    || changeStats.value == undefined
    || reportStats.value == undefined);
const error = ref(false);

async function load() {
    if (nodata.value && !error.value) {
        loadingbar.start();
        try {
            let stats = await props.data.loadStats();
            distributionStats.value = stats.distributions;
            apiStats.value = stats.apis;
            changeStats.value = stats.changes;
            reportStats.value = stats.reports;

            publicVars({ "stats": stats });

            loadingbar.finish();
        }
        catch {
            message.error(`Failed to load trends.`);
            loadingbar.error();
            error.value = true;
        }
    }
}

function buildLineChartSingle(data: { [key: string]: { [key: string]: number } }, labels: string[], config?: (type: string) => { [key: string]: any }) {
    let values: { [key: string]: number[] } = {};
    let types = new Set<string>();
    for (let label of labels) {
        Object.keys(data[label] ?? {}).forEach(x => types.add(x));
    }
    for (let type of types) {
        values[type] = [];
    }
    for (let label of labels) {
        let result = data[label] ?? {};
        for (let type of types) {
            values[type].push(result[type] ?? 0);
        }
    }

    let datasets = [];
    for (let type of types) {
        datasets.push({
            label: `${type} (${(values[type].length > 0 ? numberAverage(values[type]) : 0).toFixed(2)}, ${numberSum(values[type]).toFixed(2)})`,
            data: values[type],
            borderColor: hashedColor(type),
            backgroundColor: hashedColor(type),
            tension: 0.1,
            ...(config ? config(type) ?? {} : {})
        });
    }
    return {
        labels: labels,
        datasets: datasets,
    };
}

onMounted(() => load());

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
