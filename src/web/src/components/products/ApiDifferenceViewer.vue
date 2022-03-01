<script setup lang="ts">
import { ref, computed, onMounted, h, defineComponent } from 'vue'
import { NPageHeader, NSpace, NText, DataTableColumns, NDataTable, NBreadcrumb, NCollapseTransition, NPopover, NIcon, NLayoutContent, NAvatar, NLog, NSwitch, NStatistic, NTabs, NTabPane, NCard, NButton, useOsTheme, useMessage, NDescriptions, NDescriptionsItem, NSpin, NDrawer, NDrawerContent } from 'naive-ui'
import { HomeIcon, RootIcon, LogIcon, ReportIcon } from '../../components/icons'
import { useRouter, useRoute } from 'vue-router'
import HomeBreadcrumbItem from '../../components/breadcrumbs/HomeBreadcrumbItem.vue'
import DiffBreadcrumbItem from '../../components/breadcrumbs/DiffBreadcrumbItem.vue'
import ReleasePairBreadcrumbItem from '../../components/breadcrumbs/ReleasePairBreadcrumbItem.vue'
import { useStore } from '../../services/store'
import { ApiDifference, Distribution, ProducerOptions, Release, ReleasePair, Report } from '../../models'
import NotFound from '../../components/NotFound.vue'
import MetadataViewer from '../../components/metadata/MetadataViewer.vue'
import DistributionViewer from '../../components/products/DistributionViewer.vue'
import PaginationList from '../../components/PaginationList.vue'
import DiffEntryViewer from '../../components/entries/DiffEntryViewer.vue'
import ApiEntryViewer from '../../components/entries/ApiEntryViewer.vue'
import { BreakingRank, DiffEntry } from '../../models/difference'
import { ApiEntry } from '../../models/description'

const store = useStore();
const router = useRouter();
const route = useRoute();
const message = useMessage();

const props = defineProps<{
    data: ApiDifference,
    showDists: boolean,
    showCounts: boolean,
}>();

const sortedEntries = computed(() => {
    return Object.values(props.data.entries).sort((a, b) => {
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
        return 0;
    })
});

function rankViewer(rank: BreakingRank) {
    switch (rank) {
        case BreakingRank.Unknown: return h(NText, { type: 'default' }, 'Unknown');
        case BreakingRank.Compatible: return h(NText, { type: 'success' }, 'Compatible');
        case BreakingRank.Low: return h(NText, { type: 'info' }, 'Low');
        case BreakingRank.Medium: return h(NText, { type: 'warning' }, 'Medium');
        case BreakingRank.High: return h(NText, { type: 'error', strong: true }, 'High');
    }
}

const columns: DataTableColumns<DiffEntry> = [
    {
        title: 'Rank',
        key: 'rank',
        render(row) {
            return rankViewer(row.rank);
        }
    },
    {
        title: 'Kind',
        key: 'kind',
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
    {
        title: 'Message',
        key: 'message'
    },
    {
        title: 'Old',
        key: 'old',
        render(row) {
            if (row.old) {
                return h(
                    NPopover,
                    {},
                    {
                        trigger: () => row.old.name,
                        default: () => h(ApiEntryViewer, { entry: row.old })
                    }
                );
            }
            return "";
        }
    },
    {
        title: 'New',
        key: 'new',
        render(row) {
            if (row.new) {
                return h(
                    NPopover,
                    {},
                    {
                        trigger: () => h(NText, { type: "default" }, row.new.name),
                        default: () => h(ApiEntryViewer, { entry: row.new })
                    }
                );
            }
            return "";
        }
    },
];

</script>

<template>
    <n-space vertical size="large">
        <n-collapse-transition :show="showDists">
            <n-space>
                <DistributionViewer v-if="data.old" :data="data.old" />
                <DistributionViewer v-if="data.new" :data="data.new" />
            </n-space>
        </n-collapse-transition>
        <n-collapse-transition :show="showCounts">
            <n-space vertical>
                <n-space>
                    <n-statistic
                        v-for="rank in data.ranks()"
                        :key="rank"
                        :value="data.rank(rank).length"
                    >
                        <template #label>
                            <n-text v-if="rank == BreakingRank.Compatible" type="success">Compatible</n-text>
                            <n-text v-else-if="rank == BreakingRank.Low" type="info">Low</n-text>
                            <n-text v-else-if="rank == BreakingRank.Medium" type="warning">Medium</n-text>
                            <n-text v-else-if="rank == BreakingRank.High" type="error" strong>High</n-text>
                            <n-text v-else>Unknown</n-text>
                        </template>
                        <template #suffix>/ {{ Object.keys(data.entries).length }}</template>
                    </n-statistic>
                </n-space>
                <n-space>
                    <n-statistic
                        v-for="kind in data.kinds()"
                        :key="kind"
                        :label="kind"
                        :value="data.kind(kind).length"
                    ></n-statistic>
                </n-space>
            </n-space>
        </n-collapse-transition>

        <n-data-table :columns="columns" :data="sortedEntries"></n-data-table>
    </n-space>
</template>
