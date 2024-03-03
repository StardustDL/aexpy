<script setup lang="ts">
import { ref, computed, onMounted, h, reactive, watch } from 'vue'
import { NPageHeader, NFlex, NTooltip, NButtonGroup, NBreadcrumb, NModal, NIcon, NBackTop, useLoadingBar, NAvatar, NLog, NSwitch, NButton, useMessage, NSpin, NDrawer, NDrawerContent } from 'naive-ui'
import { NText, NDivider, DataTableColumns, NDataTable, DataTableBaseColumn, NScrollbar, NCollapseTransition, NPopover, NInputGroup, NInput, NCode } from 'naive-ui'
import { DataIcon, GoIcon, DistributionIcon, DescriptionIcon, LogIcon, DiffIcon, ReportIcon, CountIcon, EvaluateIcon } from '../../components/icons'
import { useRouter, useRoute } from 'vue-router'
import HomeBreadcrumbItem from '../../components/breadcrumbs/HomeBreadcrumbItem.vue'
import ProjectBreadcrumbItem from '../../components/breadcrumbs/ProjectBreadcrumbItem.vue'
import ReleasePairBreadcrumbItem from '../../components/breadcrumbs/ReleasePairBreadcrumbItem.vue'
import { useStore } from '../../services/store'
import { DefaultPaginationProps } from '../../services/ui'
import { ApiDifference, ReleasePair, Release, Report } from '../../models'
import NotFound from '../../components/NotFound.vue'
import MetadataViewer from '../../components/metadata/MetadataViewer.vue'
import { publicVars, apiUrl, changeUrl, hashedColor } from '../../services/utils'
import DistributionSwitch from '../../components/switches/DistributionSwitch.vue'
import LogSwitchPanel from '../../components/switches/LogSwitchPanel.vue'
import StaticticsSwitch from '../../components/switches/StatisticsSwitch.vue'
import DistributionLink from '../../components/links/DistributionLink.vue'
import DescriptionLink from '../../components/links/DescriptionLink.vue'
import ReportLink from '../../components/links/ReportLink.vue'
import DistributionViewer from '../../components/products/DistributionViewer.vue'
import ApiEntryViewer from '../../components/entries/ApiEntryViewer.vue'
import { BreakingRank, DiffEntry, getRankColor } from '../../models/difference'
import CountViewer from '../../components/metadata/CountViewer.vue'
import { DoughnutChart } from 'vue-chart-3';
import ApiEntryLink from '../../components/links/ApiEntryLink.vue'
import DiffEntryLink from '../../components/links/DiffEntryLink.vue'
import ReleasePairPrevSuccLink from '../../components/links/ReleasePairPrevSuccLink.vue'

const store = useStore();
const router = useRouter();
const route = useRoute();
const message = useMessage();
const loadingbar = useLoadingBar();

const props = defineProps<{
    project: string,
    old: string,
    new: string,
}>();
const release = computed(() => new ReleasePair(new Release(props.project, props.old), new Release(props.project, props.new)));

const entry = computed(() => route.query.entry?.toString());

const showDists = ref<boolean>(false);
const showStats = ref<boolean>(true);
const showReport = ref<boolean>(false);

const data = ref<ApiDifference>();
const error = ref<boolean>(false);
const reportData = ref<Report>();

const sortedEntries = computed(() => {
    let rawData = data.value || new ApiDifference();
    return Object.values(rawData.entries).sort((a, b) => {
        if (entry) {
            if (a.id == entry.value && b.id != entry.value) {
                return -1;
            }
            if (b.id == entry.value && a.id != entry.value) {
                return 1;
            }
        }
        if (a.rank > b.rank) {
            return -1;
        }
        if (a.rank < b.rank) {
            return 1;
        }
        if (a.kind < b.kind) {
            return -1;
        }
        if (a.kind > b.kind) {
            return 1;
        }
        if (a.message < b.message) {
            return -1;
        }
        if (a.message > b.message) {
            return 1;
        }
        return 0;
    })
});

function rankViewer(rank: BreakingRank) {
    switch (rank) {
        case BreakingRank.Unknown: return h(NText, { type: 'default' }, { default: () => '❔' });
        case BreakingRank.Compatible: return h(NText, { type: 'success' }, { default: () => '🟢' });
        case BreakingRank.Low: return h(NText, { type: 'info' }, { default: () => '🟡' });
        case BreakingRank.Medium: return h(NText, { type: 'warning' }, { default: () => '🟠' });
        case BreakingRank.High: return h(NText, { type: 'error', strong: true }, { default: () => '🔴' });
    }
}

const messageFilterValue = ref("");

const columns = computed(() => {
    let rawData = data.value || new ApiDifference();

    let kinds = rawData.kinds();
    let kindFilterOptions = kinds.sort().map(kind => { return { label: kind, value: kind }; });
    let rankFilterOptions = rawData.ranks().sort().map(rank => { return { label: rankViewer(rank), value: rank }; });

    let messageColumn = reactive<DataTableBaseColumn<DiffEntry>>({
        title: 'Message',
        key: 'message',
        width: 800,
        sorter: "default",
        filter: "default",
        filterOptionValue: "",

        render: (row) => {
            return h(
                NPopover,
                {},
                {
                    trigger: () => h(NText, {}, { default: () => (row.id == entry.value ? "⭐ " : "") + row.message }),
                    default: () => h(NScrollbar,
                        { style: "max-height: 500px; max-width: 500px;", "x-scrollable": true },
                        {
                            default: () => h(NCode, { language: "json", code: JSON.stringify(row.data, undefined, 2) }),
                        }),
                }
            )
        },
        renderFilterMenu: ({ hide }) => {
            return h(
                NInputGroup,
                {},
                {
                    default: () => [
                        h(
                            NInput,
                            {
                                onUpdateValue: (value) => {
                                    messageFilterValue.value = value;
                                },
                                value: messageFilterValue.value,
                                clearable: true,
                            },
                        ),
                        h(
                            NButton,
                            {
                                onClick: () => {
                                    if (messageFilterValue.value.length == 0) {
                                        messageColumn.filterOptionValue = null;
                                    }
                                    else {
                                        messageColumn.filterOptionValue = messageFilterValue.value;
                                    }
                                    hide();
                                }
                            },
                            {
                                default: () => h(NIcon, { component: GoIcon }, {})
                            }
                        )
                    ]
                }
            )
        }
    });

    return [
        {
            key: 'rank',
            width: 50,
            sorter: "default",
            filterOptions: rankFilterOptions,
            defaultFilterOptionValues: rawData.ranks(),
            filter: "default",
            render(row) {
                return h(NFlex, {}, {
                    default: () => rankViewer(row.rank)
                });
            }
        },
        {
            title: 'Kind',
            key: 'kind',
            width: 200,
            sorter: "default",
            filterOptions: kindFilterOptions,
            defaultFilterOptionValues: kinds,
            filter: "default",
            render: (row) => {
                return h(
                    NPopover,
                    {},
                    {
                        trigger: () => row.kind,
                        default: () => h(DiffEntryLink, { entry: row.id, url: changeUrl(new ReleasePair(rawData.old.release, rawData.new.release)) }, {}),
                    }
                )
            }
        },
        messageColumn,
        {
            title: 'Old',
            key: 'old',
            width: 80,
            sorter(row1, row2) {
                if ((row1.old ?? "") == (row2.old ?? ""))
                    return 0;
                return (row1.old ?? "") < (row2.old ?? "") ? -1 : 1;
            },
            render(row) {
                if (row.old) {
                    return h(
                        NPopover,
                        {},
                        {
                            trigger: () => {
                                if (row.old) {
                                    return h(ApiEntryLink, { entry: row.old.id, url: apiUrl(rawData.old.release), text: false, icon: true }, {})
                                }
                                return "";
                            },
                            default: () => {
                                if (row.old) {
                                    let old = row.old;
                                    return h(NScrollbar,
                                        { style: "max-height: 500px; max-width: 800px;", "x-scrollable": true },
                                        {
                                            default: () => h(ApiEntryViewer, {
                                                entry: old,
                                                rawUrl: rawData.old.rootPath,
                                                entryUrl: apiUrl(rawData.old.release),
                                            })
                                        });
                                }
                                return "";
                            },
                        }
                    );
                }
                return "";
            }
        },
        {
            title: 'New',
            key: 'new',
            width: 80,
            sorter(row1, row2) {
                if ((row1.new ?? "") == (row2.new ?? ""))
                    return 0;
                return (row1.new ?? "") < (row2.new ?? "") ? -1 : 1;
            },
            render(row) {
                if (row.new) {
                    return h(
                        NPopover,
                        {},
                        {
                            trigger: () => {
                                if (row.new) {
                                    return h(ApiEntryLink, { entry: row.new.id, url: apiUrl(rawData.new.release), text: false, icon: true }, {})
                                }
                                return "";
                            },
                            default: () => {
                                if (row.new) {
                                    let ne = row.new;
                                    return h(NScrollbar,
                                        { style: "max-height: 500px; max-width: 800px;", "x-scrollable": true },
                                        {
                                            default: () => h(ApiEntryViewer, {
                                                entry: ne,
                                                rawUrl: rawData.new.rootPath,
                                                entryUrl: apiUrl(rawData.new.release),
                                            })
                                        });
                                }
                                return "";
                            },
                        }
                    );
                }
                return "";
            }
        },
    ] as DataTableColumns<DiffEntry>;
});

function getRankType(rank: BreakingRank) {
    switch (rank) {
        case BreakingRank.Compatible: return 'success';
        case BreakingRank.Low: return 'info';
        case BreakingRank.Medium: return 'warning';
        case BreakingRank.High: return 'error';
        default: return 'default';
    }
}

const kindCounts = computed(() => {
    let rawData = data.value || new ApiDifference();
    let raw = [];
    let kinds = [];
    let bgs = []
    for (let kind of rawData.kinds()) {
        let count = rawData.kind(kind).length;
        kinds.push(kind);
        raw.push(count);
        bgs.push(hashedColor(kind));
    }
    return {
        labels: kinds,
        datasets: [
            {
                data: raw,
                backgroundColor: bgs,
            },
        ],
    };
});

const bckindCounts = computed(() => {
    let rawData = data.value || new ApiDifference();
    let raw = [];
    let kinds = [];
    let bgs = []
    for (let kind of rawData.kinds()) {
        let count = rawData.kind(kind).filter((value) => value.rank >= BreakingRank.Low).length;
        if (count > 0) {
            kinds.push(kind);
            raw.push(count);
            bgs.push(hashedColor(kind));
        }
    }
    return {
        labels: kinds,
        datasets: [
            {
                data: raw,
                backgroundColor: bgs,
            },
        ],
    };
});

const rankCounts = computed(() => {
    let rawData = data.value || new ApiDifference();
    let raw = [];
    let ranks = [];
    let bgs = []
    for (let rank of rawData.ranks()) {
        let count = rawData.rank(rank).length;
        ranks.push(BreakingRank[rank]);
        raw.push(count);
        bgs.push(getRankColor(rank));
    }
    return {
        labels: ranks,
        datasets: [
            {
                data: raw,
                backgroundColor: bgs,
            },
        ],
    };
});

async function load() {
    data.value = undefined;
    error.value = false;
    reportData.value = undefined;

    loadingbar.start();
    try {
        data.value = await store.state.api.change(release.value);
        publicVars({ "data": data.value });
    }
    catch (e) {
        console.error(e);
        error.value = true;
        message.error(`Failed to load diffed data for ${release.value}.`);
    }

    if (error.value) {
        loadingbar.error();
    }
    else {
        loadingbar.finish();
    }
}

onMounted(async () => await load());
watch(release, () => load());

async function onReport(value: boolean) {
    if (!value || reportData.value) return;
    try {
        reportData.value = await store.state.api.report(release.value);
        publicVars({ "report": reportData.value });
    }
    catch {
        message.error(`Failed to load report for ${release}.`);
    }
}
</script>

<template>
    <n-flex vertical>
        <n-page-header :title="release?.toString() ?? 'Unknown'" subtitle="API Difference" @back="() => router.back()">
            <template #avatar>
                <n-avatar>
                    <n-icon :component="DiffIcon" />
                </n-avatar>
            </template>

            <template #header>
                <n-breadcrumb>
                    <HomeBreadcrumbItem />
                    <ProjectBreadcrumbItem />
                    <ReleasePairBreadcrumbItem :release="release" />
                </n-breadcrumb>
            </template>

            <template #footer>
                <n-flex v-if="data" :align="'center'">
                    <MetadataViewer :data="data" />
                    <n-button-group size="small" v-if="release">
                        <ReleasePairPrevSuccLink :pair="release" kind="diffed" />
                        <DistributionLink :release="release.old" />
                        <DescriptionLink :release="release.old" />
                        <DistributionLink :release="release.new" />
                        <DescriptionLink :release="release.new" />
                        <ReportLink :pair="release" />
                    </n-button-group>
                    <DistributionSwitch v-model="showDists" />
                    <StaticticsSwitch v-model="showStats" />
                    <n-tooltip>
                        <template #trigger>
                            <n-switch v-model:value="showReport" @update-value="onReport">
                                <template #checked>
                                    <n-icon size="large" :component="ReportIcon" />
                                </template>

                                <template #unchecked>
                                    <n-icon size="large" :component="ReportIcon" />
                                </template>
                            </n-switch>
                        </template>
                        Report
                    </n-tooltip>
                    <LogSwitchPanel :load="() => store.state.api.changeLog(release)" />
                    <CountViewer :value="data.breaking().length" label="Breaking" inline
                        :total="Object.keys(data.entries).length" status="warning"></CountViewer>
                </n-flex>
            </template>
        </n-page-header>

        <NotFound v-if="error" :path="router.currentRoute.value.fullPath" size="huge"></NotFound>
        <n-spin v-else-if="!data" :size="160" style="width: 100%; margin: 50px"></n-spin>

        <n-flex vertical v-if="data">
            <n-collapse-transition :show="showDists">
                <n-divider>
                    <n-flex :wrap="false" :align="'center'">
                        <n-icon size="large" :component="DistributionIcon" />
                        Distributions
                    </n-flex>
                </n-divider>
                <n-flex>
                    <DistributionViewer v-if="data.old" :data="data.old" />
                    <DistributionViewer v-if="data.new" :data="data.new" />
                </n-flex>
            </n-collapse-transition>
            <n-collapse-transition :show="showStats">
                <n-divider>
                    <n-flex :wrap="false" :align="'center'">
                        <n-icon size="large" :component="CountIcon" />
                        Statistics
                    </n-flex>
                </n-divider>
                <n-flex>
                    <DoughnutChart :chart-data="rankCounts"
                        :options="{ plugins: { legend: { position: 'bottom' }, title: { display: true, text: 'Ranks' } } }"
                        v-if="Object.keys(data.entries).length > 0" />
                    <DoughnutChart :chart-data="bckindCounts"
                        :options="{ plugins: { legend: { position: 'bottom' }, title: { display: true, text: 'Breaking Kinds' } } }"
                        v-if="Object.keys(data.entries).length > 0 && data.breaking().length > 0" />
                    <DoughnutChart :chart-data="kindCounts"
                        :options="{ plugins: { legend: { position: 'bottom' }, title: { display: true, text: 'Kinds' } } }"
                        v-if="Object.keys(data.entries).length > 0" />
                </n-flex>
            </n-collapse-transition>

            <n-data-table :columns="columns" :data="sortedEntries" :pagination="DefaultPaginationProps"
                striped></n-data-table>
        </n-flex>

        <n-modal v-model:show="showReport" preset="card" title="Report">
            <n-spin v-if="reportData == undefined" :size="60" style="width: 100%"></n-spin>
            <n-scrollbar v-else style="max-height: 500px">
                <pre style="font-size: larger;">{{ reportData.content }}</pre>
            </n-scrollbar>
        </n-modal>
    </n-flex>
</template>
