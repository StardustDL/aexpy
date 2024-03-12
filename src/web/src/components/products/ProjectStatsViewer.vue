<script setup lang="ts">
import { ref, computed, onMounted, Ref, h, watch } from 'vue'
import { NPageHeader, NFlex, NSpace, NText, useLoadingBar, NDivider, NInputGroupLabel, NSwitch, NInputGroup, NTab, NTabs, NStatistic, useMessage, NSpin, NSelect, SelectOption, SelectRenderTag, NTag } from 'naive-ui'
import { Distribution, Release, ApiDescription, ApiDifference, Report, ReleasePair, ProduceState, ProjectProductIndex, PackageStats, PackageProductStats } from '../../models'
import { numberSum, numberAverage, publicVars, apiUrl, changeUrl, distributionUrl, reportUrl, hashedColor } from '../../services/utils'
import NotFound from '../../components/NotFound.vue'
import CountViewer from '../../components/metadata/CountViewer.vue'
import { LineChart } from 'vue-chart-3'
import { BreakingRank, getRankColor } from '../../models/difference'
import { AttributeEntry, FunctionEntry, getTypeColor } from '../../models/description'
import { useStore } from '../../services/store'

const props = defineProps<{ data: ProjectProductIndex }>();
const stats = ref<PackageStats>();
const selectKeys = ref<string[] | string>(["duration"]);
const selectStats = ref<"Distribution" | "API" | "Change" | "Report">("Distribution");
const selectKeyKind = ref<"Single" | "Multiple">("Single");

const store = useStore();
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

const selectStatOptions = computed(() => {
    let res: SelectOption[] = [];
    for (let val of ["Distribution", "API", "Change", "Report"]) {
        res.push({
            label: val,
            value: val
        });
    }
    return res;
});

const selectKeyKindOptions = computed(() => {
    let res: SelectOption[] = [];
    for (let val of ["Single", "Multiple"]) {
        res.push({
            label: val,
            value: val
        });
    }
    return res;
});

const currentStats = computed(() => {
    switch (selectStats.value) {
        case "Distribution":
            return stats.value?.dists;
        case "API":
            return stats.value?.apis;
        case "Change":
            return stats.value?.changes;
        case "Report":
            return stats.value?.reports;
        default:
            return;
    }
});

const currentLabels = computed(() => {
    switch (selectStats.value) {
        case "Distribution":
            return props.data.preprocessed.map(s => s.toString());
        case "API":
            return props.data.extracted.map(s => s.toString());
        case "Change":
            return props.data.diffed.map(s => s.toString());
        case "Report":
            return props.data.reported.map(s => s.toString());
        default:
            return [];
    }
});

const selectKeyOptions = computed(() => {
    if (!currentStats.value) return [];
    let res: SelectOption[] = [];
    let keys = currentStats.value.singleKeys;
    if (selectKeyKind.value == "Multiple") keys = currentStats.value.multipleKeys;
    for (let key of keys) {
        res.push({
            label: key,
            value: key,
        })
    }
    return res;
});

const renderSelectKeyTag: SelectRenderTag = ({ option, handleClose }) => {
    return h(
        NTag,
        {
            closable: true,
            color: { color: hashedColor(option.value!.toString()), textColor: "white" },
            onMousedown: (e: FocusEvent) => {
                e.preventDefault()
            },
            onClose: (e: MouseEvent) => {
                e.stopPropagation()
                handleClose()
            }
        },
        { default: () => option.label }
    )
}

const customChartData = ref();

function buildCustomCharData() {
    customChartData.value = undefined;

    setTimeout(() => {
        if (currentStats.value) {
            let data: StatType = {};
            if (selectKeyKind.value == "Single") {
                data = currentStats.value.selectMany(...selectKeys.value);
            } else {
                data = currentStats.value.select(<string>selectKeys.value);
            }
            customChartData.value = buildLineChartSingle(data, currentLabels.value, (t) => {
                return {};
            });
        }
    });
}
watch(selectKeys, buildCustomCharData);

const singleDurations = computed(() => {
    let data: StatType = {};
    if (stats.value) {
        data = combineStats(data, stats.value.dists.selectMany<number>(["duration", "preprocess"]));
        data = combineStats(data, stats.value.apis.selectMany<number>(["duration", "extract"]));
    }
    return buildLineChartSingle(data, props.data.releases.map(x => x.toString()), (t) => {
        return { fill: true };
    });
});
const pairDurations = computed(() => {
    let data: StatType = {};
    if (stats.value) {
        data = combineStats(data, stats.value.changes.selectMany<number>(["duration", "diff"]));
        data = combineStats(data, stats.value.reports.selectMany<number>(["duration", "report"]));
    }
    return buildLineChartSingle(data, props.data.pairs.map(x => x.toString()), (t) => {
        return { fill: true };
    });
});
const locCounts = computed(() => {
    if (stats.value) {
        let data: StatType = stats.value.dists.selectMany<number>("loc", ["filesize", "size"]);
        return buildLineChartSingle(data, props.data.preprocessed.map(x => x.toString()), (t) => {
            return { yAxisID: t }
        });
    }
});
const entryCounts = computed(() => {
    if (stats.value) {
        let data: StatType = stats.value.apis.selectMany<number>(
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
    if (stats.value) {
        let data: StatType = stats.value.apis.selectMany<number>(
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
    if (stats.value) {
        let data: StatType = stats.value.changes.select("ranks");
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
    if (stats.value) {
        let data: StatType = stats.value.changes.select("kinds");
        return buildLineChartSingle(data, props.data.diffed.map(x => x.toString()), (t) => {
            return {
                fill: true,
            }
        });
    }
});
const bckindCounts = computed(() => {
    if (stats.value) {
        let data: StatType = stats.value.changes.select("breaking_kinds");
        return buildLineChartSingle(data, props.data.diffed.map(x => x.toString()), (t) => {
            return {
                fill: true,
            }
        });
    }
});
const bcCount = computed(() => {
    if (stats.value) {
        return numberSum(Object.values(stats.value.changes.select<number>("breaking")));
    }
    return 0;
});
const bcTypeCount = computed(() => {
    let result = 0;
    if (stats.value) {
        let data: StatType = stats.value.changes.select("breaking_kinds");
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
    if (stats.value) {
        let data: StatType = stats.value.changes.select("breaking_kinds");
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
    if (stats.value) {
        let data: StatType = stats.value.changes.select("breaking_kinds");
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
    if (stats.value) {
        let data: StatType = stats.value.changes.select("breaking_kinds");
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
    if (!stats.value) {
        return 0.0;
    }
    let calc = (raw: PackageProductStats) => {
        let values = Object.values(raw.select<number>("duration"));
        if (values.length > 0) {
            return numberAverage(values);
        }
        return 0.0;
    }
    return (calc(stats.value.dists) + calc(stats.value.apis)) * 2 + calc(stats.value.changes) + calc(stats.value.reports);
});
const maxTotalDuration = computed(() => {
    if (!stats.value) {
        return 0.0;
    }
    let calc = (raw: PackageProductStats) => {
        let values = Object.values(raw.select<number>("duration"));
        if (values.length > 0) {
            return Math.max(...values);
        }
        return 0.0;
    }
    return (calc(stats.value.dists) + calc(stats.value.apis)) * 2 + calc(stats.value.changes) + calc(stats.value.reports);
});

const error = ref(false);

async function load() {
    if (!stats.value && !error.value) {
        loadingbar.start();
        try {
            stats.value = await store.state.api.package(props.data.project).stats();

            publicVars({ "stats": stats });

            loadingbar.finish();
        }
        catch {
            message.error(`Failed to load trends.`);
            loadingbar.error();
            error.value = true;
        }
        buildCustomCharData();
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

    <n-spin v-else-if="!stats" :size="160" style="width: 100%; margin: 50px"></n-spin>

    <n-flex v-else vertical>
        <n-input-group>
            <n-select v-model:value="selectStats" :style="{ width: '150px' }" :options="selectStatOptions"
                placeholder="Product" />
            <n-select v-model:value="selectKeyKind" :style="{ width: '150px' }" :options="selectKeyKindOptions"
                placeholder="Key Kind" />
            <n-select v-model:value="selectKeys" :multiple="selectKeyKind == 'Single'" clearable
                :options="selectKeyOptions" placeholder="Keys" :render-tag="renderSelectKeyTag" />
        </n-input-group>

        <n-flex vertical>
            <LineChart :chart-data="customChartData"
                :options="{ plugins: { legend: { position: 'bottom' }, title: { display: true, text: 'Custom Data' } } }"
                v-if="customChartData"></LineChart>
            <n-spin v-else :size="160" style="width: 100%; margin: 50px"></n-spin>
        </n-flex>

        <n-divider></n-divider>
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
