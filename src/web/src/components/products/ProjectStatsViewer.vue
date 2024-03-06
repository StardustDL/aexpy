<script setup lang="ts">
import { ref, computed, onMounted, Ref } from 'vue'
import { NPageHeader, NFlex, NSpace, NText, useLoadingBar, NStatistic, useMessage, NSpin } from 'naive-ui'
import { Distribution, Release, ApiDescription, ApiDifference, Report, ReleasePair, ProduceState, PackageProductIndex, PackageStats } from '../../models'
import { numberSum, numberAverage, publicVars, apiUrl, changeUrl, distributionUrl, reportUrl, hashedColor } from '../../services/utils'
import NotFound from '../../components/NotFound.vue'
import CountViewer from '../../components/metadata/CountViewer.vue'
import { LineChart } from 'vue-chart-3'
import { BreakingRank, getRankColor } from '../../models/difference'
import { AttributeEntry, FunctionEntry, getTypeColor } from '../../models/description'

const props = defineProps<{ data: PackageProductIndex }>();
const distriubtionStats = ref<PackageStats>();
const apiStats = ref<PackageStats>();
const changeStats = ref<PackageStats>();
const reportStats = ref<PackageStats>();

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

const avgTotalDuration = computed(() => {
    let calc = (raw: Ref<PackageStats | undefined>) => {
        if (raw.value) {
            let values = Object.values(raw.value.select<number>("duration"));
            if (values.length > 0) {
                return values.reduce((x, y) => x + y, 0) / values.length;
            }
        }
        return 0.0;
    }
    return (calc(distriubtionStats) + calc(apiStats)) * 2 + calc(changeStats) + calc(reportStats);
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
    return (calc(distriubtionStats) + calc(apiStats)) * 2 + calc(changeStats) + calc(reportStats);
});

const nodata = computed(() => distriubtionStats.value == undefined
    || apiStats.value == undefined
    || changeStats.value == undefined
    || reportStats.value == undefined);
const error = ref(false);

async function load() {
    if (nodata.value && !error.value) {
        loadingbar.start();
        try {
            let stats = await props.data.loadStats();
            distriubtionStats.value = stats.distributions;
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
