<script setup lang="ts">
import { ref, computed, onMounted, h, defineComponent, reactive } from 'vue'
import { NSpace, NText, NDivider, DataTableColumns, NDataTable, DataTableBaseColumn, NScrollbar, NCollapseTransition, NPopover, NIcon, NButton, NInputGroup, NInput, NCode } from 'naive-ui'
import { GoIcon, VerifiedIcon, UnverifiedIcon, NoverifyIcon } from '../../components/icons'
import { ApiDifference} from '../../models'
import { hashedColor } from '../../services/utils'
import DistributionViewer from '../../components/products/DistributionViewer.vue'
import ApiEntryViewer from '../../components/entries/ApiEntryViewer.vue'
import { BreakingRank, DiffEntry, getRankColor, getVerifyColor, VerifyState } from '../../models/difference'
import CountViewer from '../metadata/CountViewer.vue'
import { DoughnutChart } from 'vue-chart-3';
import VerifyDataViewer from '../metadata/VerifyDataViewer.vue'
import ApiEntryLink from '../metadata/ApiEntryLink.vue'

const props = defineProps<{
    data: ApiDifference,
    showDists: boolean,
    showStats: boolean,
}>();

const sortedEntries = computed(() => {
    return Object.values(props.data.entries).sort((a, b) => {
        if (a.rank > b.rank) {
            return -1;
        }
        if (a.rank < b.rank) {
            return 1;
        }
        // if (a.verify.state > b.verify.state) {
        //     return -1;
        // }
        // if (a.verify.state < b.verify.state) {
        //     return 1;
        // }
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

function verifyViewer(verify: VerifyState) {
    switch (verify) {
        case VerifyState.Unknown: return h(NIcon, { color: getVerifyColor(verify) }, { default: () => h(NoverifyIcon) });
        case VerifyState.Pass: return h(NIcon, { color: getVerifyColor(verify) }, { default: () => h(VerifiedIcon) });
        case VerifyState.Fail: return h(NIcon, { color: getVerifyColor(verify) }, { default: () => h(UnverifiedIcon) });
    }
}

const messageFilterValue = ref("");

const columns = computed(() => {
    let kinds = props.data.kinds();
    let kindFilterOptions = kinds.sort().map(kind => { return { label: kind, value: kind }; });
    let rankFilterOptions = props.data.ranks().sort().map(rank => { return { label: rankViewer(rank), value: rank }; });
    // let verifyFilterOptions = props.data.verifies().map(verify => { return { label: verifyViewer(verify), value: verify }; });

    let messageColumn = reactive<DataTableBaseColumn<DiffEntry>>({
        title: 'Message',
        key: 'message',
        sorter: "default",
        filter: "default",
        filterOptionValue: "",

        render: (row) => {
            return h(
                NPopover,
                {},
                {
                    trigger: () => h(NText, {}, { default: () => row.message }),
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
                                default: () => h(NIcon, {}, {
                                    default: () => h(GoIcon),
                                })
                            }
                        )
                    ]
                }
            )
        }
    });

    return [
        {
            title: 'R',
            key: 'rank',
            width: 80,
            sorter: "default",
            filterOptions: rankFilterOptions,
            defaultFilterOptionValues: props.data.ranks(),
            filter: "default",
            render(row) {
                return h(NSpace, {}, {
                    default: () => [
                        rankViewer(row.rank),
                        h(
                            NPopover,
                            {},
                            {
                                trigger: () => verifyViewer(row.verify.state),
                                default: () => h(VerifyDataViewer as any, {
                                    data: row.verify
                                })
                            }
                        ),
                    ]
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
                        default: () => row.id,
                    }
                )
            }
        },
        messageColumn,
        {
            title: 'Old',
            key: 'old',
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
                                    return h(ApiEntryLink, { entry: row.old.id, url: `/apis/${props.data.old.release.toString()}/` }, {})
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
                                                rawUrl: props.data.old.rootPath,
                                                entryUrl: `/apis/${props.data.old.release.toString()}/`,
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
                                    return h(ApiEntryLink, { entry: row.new.id, url: `/apis/${props.data.new.release.toString()}/` }, {})
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
                                                rawUrl: props.data.new.rootPath,
                                                entryUrl: `/apis/${props.data.new.release.toString()}/`,
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
    let raw = [];
    let kinds = [];
    let bgs = []
    for (let kind of props.data.kinds()) {
        let count = props.data.kind(kind).length;
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
    let raw = [];
    let kinds = [];
    let bgs = []
    for (let kind of props.data.kinds()) {
        let count = props.data.kind(kind).filter((value) => value.rank >= BreakingRank.Low).length;
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
    let raw = [];
    let ranks = [];
    let bgs = []
    for (let rank of props.data.ranks()) {
        let count = props.data.rank(rank).length;
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


const verifyCounts = computed(() => {
    let raw = [];
    let verifys = [];
    let bgs = [];
    for (let rank of props.data.verifies()) {
        let count = props.data.verify(rank).filter((value) => value.rank >= BreakingRank.Low).length;
        if (count > 0) {
            verifys.push(VerifyState[rank]);
            raw.push(count);
            bgs.push(getVerifyColor(rank));
        }
    }
    return {
        labels: verifys,
        datasets: [
            {
                data: raw,
                backgroundColor: bgs,
            },
        ],
    };
});

</script>

<template>
    <n-space vertical>
        <n-collapse-transition :show="showDists">
            <n-divider>Distributions</n-divider>
            <n-space>
                <DistributionViewer v-if="data.old" :data="data.old" />
                <DistributionViewer v-if="data.new" :data="data.new" />
            </n-space>
        </n-collapse-transition>
        <n-collapse-transition :show="showStats">
            <n-divider>Statistics</n-divider>
            <n-space>
                <CountViewer
                    :value="data.breaking().length"
                    label="Breaking"
                    :total="Object.keys(data.entries).length"
                    status="warning"
                ></CountViewer>
                <DoughnutChart
                    :chart-data="rankCounts"
                    :options="{ plugins: { legend: { position: 'bottom' }, title: { display: true, text: 'Ranks' } } }"
                    v-if="Object.keys(data.entries).length > 0"
                />
                <DoughnutChart
                    :chart-data="verifyCounts"
                    :options="{ plugins: { legend: { position: 'bottom' }, title: { display: true, text: 'Breaking Verified' } } }"
                    v-if="Object.keys(data.entries).length > 0 && data.breaking().length > 0"
                />
                <DoughnutChart
                    :chart-data="bckindCounts"
                    :options="{ plugins: { legend: { position: 'bottom' }, title: { display: true, text: 'Breaking Kinds' } } }"
                    v-if="Object.keys(data.entries).length > 0 && data.breaking().length > 0"
                />
                <DoughnutChart
                    :chart-data="kindCounts"
                    :options="{ plugins: { legend: { position: 'bottom' }, title: { display: true, text: 'Kinds' } } }"
                    v-if="Object.keys(data.entries).length > 0"
                />
            </n-space>
        </n-collapse-transition>

        <n-divider>Entries</n-divider>

        <n-data-table
            :columns="columns"
            :data="sortedEntries"
            :pagination="{ pageSize: 10 }"
            striped
        ></n-data-table>
    </n-space>
</template>
