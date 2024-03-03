<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { NPageHeader, NFlex, NButtonGroup, NProgress, NTooltip, NDivider, NInput, NInputNumber, NTreeSelect, NBreadcrumb, NAutoComplete, NModal, NDrawer, NDrawerContent, NCollapseTransition, useLoadingBar, NSwitch, NLog, NIcon, NLayoutContent, NAvatar, NStatistic, NTabs, NTabPane, NCard, NButton, useOsTheme, useMessage, NDescriptions, NDescriptionsItem, NSpin, useThemeVars } from 'naive-ui'
import { CallIcon, DataIcon, DistributionIcon, SearchIcon, InheritanceIcon, CountIcon, ApiLevelIcon, ExtractIcon, LogIcon } from '../../components/icons'
import { useRouter, useRoute } from 'vue-router'
import ApiLevelViewer from '../../components/entries/ApiLevelViewer.vue';
import CallgraphViewer from '../../components/entries/CallgraphViewer.vue';
import HomeBreadcrumbItem from '../../components/breadcrumbs/HomeBreadcrumbItem.vue'
import ReleaseBreadcrumbItem from '../../components/breadcrumbs/ReleaseBreadcrumbItem.vue'
import { useStore } from '../../services/store'
import { Release, ApiDescription } from '../../models'
import NotFound from '../../components/NotFound.vue'
import MetadataViewer from '../../components/metadata/MetadataViewer.vue'
import ProjectBreadcrumbItem from '../../components/breadcrumbs/ProjectBreadcrumbItem.vue'
import DistributionViewer from '../../components/products/DistributionViewer.vue'
import ApiEntryViewer from '../../components/entries/ApiEntryViewer.vue'
import CountViewer from '../../components/metadata/CountViewer.vue'
import { DoughnutChart, BarChart } from 'vue-chart-3';
import { ApiEntry, AttributeEntry, ClassEntry, FunctionEntry, ModuleEntry } from '../../models/description'
import { publicVars, apiUrl, changeUrl, distributionUrl } from '../../services/utils'
import GlobalCallgraphViewer from '../../components/entries/GlobalCallgraphViewer.vue';
import GlobalInheritanceViewer from '../../components/entries/GlobalInheritanceViewer.vue';
import InheritanceViewer from '../../components/entries/InheritanceViewer.vue';
import DistributionSwitch from '../../components/switches/DistributionSwitch.vue'
import StaticticsSwitch from '../../components/switches/StatisticsSwitch.vue'
import LogSwitchPanel from '../../components/switches/LogSwitchPanel.vue'
import DistributionLink from '../../components/links/DistributionLink.vue'
import ReleasePrevSuccLink from '../../components/links/ReleasePrevSuccLink.vue';
import { buildApiTreeOptions, renderApiTreeLabel, filterApiTreeOption } from '../../services/ui';

const store = useStore();
const router = useRouter();
const route = useRoute();
const message = useMessage();
const loadingbar = useLoadingBar();

const props = defineProps<{
    project: string,
    version: string,
}>();
const release = computed(() => new Release(props.project, props.version));

const showDists = ref<boolean>(false);
const showStats = ref<boolean>(true);
const showCallgraph = ref<boolean>(false);
const showCallgraphCallee = ref<boolean>(true);
const showCallgraphCaller = ref<boolean>(true);
const showCallgraphExternal = ref<boolean>(true);
const callgraphDepth = ref<number>(2);
const showApiLevel = ref<boolean>(false);
const apiLevelSearchPattern = ref<string>("");
const showInheritance = ref<boolean>(false);
const showInheritanceSub = ref<boolean>(true);
const showInheritanceBase = ref<boolean>(true);
const showInheritanceExternal = ref<boolean>(true);
const inheritanceDepth = ref<number>(2);

const data = ref<ApiDescription>();
const error = ref<boolean>(false);

function loadFromRouteQuery() {
    if (!data.value) return;
    if (route.query.entry) {
        currentEntryId.value = route.query.entry.toString();
    }
    else {
        if (data.value.distribution.topModules.length > 0) {
            let topModule = data.value.distribution.topModules[0];
            if (data.value.entry(topModule)) {
                currentEntryId.value = topModule;
            }
        }
    }

    if (route.query.tab) {
        switch (route.query.tab) {
            case "level":
                showApiLevel.value = true;
                break;
            case "callgraph":
                showCallgraph.value = true;
                break;
            case "inheritance":
                showInheritance.value = true;
                break;
        }
    }
}

async function load() {
    data.value = undefined;
    error.value = false;

    loadingbar.start();
    try {
        data.value = await store.state.api.api(release.value);
        publicVars({ "data": data.value });
    }
    catch (e) {
        console.error(e);
        error.value = true;
        message.error(`Failed to load extracted data for ${release.value}.`);
    }

    if (error.value) {
        loadingbar.error();
    }
    else {
        loadingbar.finish();
    }

    loadFromRouteQuery();
}

onMounted(async () => await load());
watch(release, () => load());
watch(() => route.query, loadFromRouteQuery);

const currentEntryId = ref<string>("");
const currentEntry = computed(() => data.value?.entry(currentEntryId.value));
const entryTreeOptions = computed(() => {
    if (!data.value) {
        return [];
    }
    return buildApiTreeOptions(data.value,)
});

const entryCounts = computed(() => {
    let raw: { label: string, data: number, backgroundColor: string }[] = [];
    if (data.value) {
        let modules = Object.values(data.value.modules);
        let classes = Object.values(data.value.classes);
        let funcs = Object.values(data.value.functions);
        let attrs = Object.values(data.value.attributes);

        raw = raw.concat([
            {
                label: "Modules",
                data: modules.filter(x => !x.private).length,
                backgroundColor: '#2080f0',
            },
            {
                label: "Private Modules",
                data: modules.filter(x => x.private).length,
                backgroundColor: '#2080f050',
            },
            {
                label: "Classes",
                data: classes.filter(x => !x.private).length,
                backgroundColor: '#f0a020',
            },
            {
                label: "Private Classes",
                data: classes.filter(x => x.private).length,
                backgroundColor: '#f0a02050',
            },
            {
                label: "Functions",
                data: funcs.filter(x => !x.private).length,
                backgroundColor: '#18a058',
            },
            {
                label: "Private Functions",
                data: funcs.filter(x => x.private).length,
                backgroundColor: '#18a05850',
            },
            {
                label: "Attributes",
                data: attrs.filter(x => !x.private).length,
                backgroundColor: '#d03050',
            },
            {
                label: "Private Attributes",
                data: attrs.filter(x => x.private).length,
                backgroundColor: '#d0305050',
            },
        ]);
    }
    raw = raw.filter(x => x.data > 0);
    return {
        labels: raw.map(x => x.label),
        datasets: [
            {
                data: raw.map(x => x.data),
                backgroundColor: raw.map(x => x.backgroundColor),
            },
        ],
    };
});
const boundEntryCounts = computed(() => {
    let raw = [0, 0, 0, 0, 0, 0];
    if (data.value) {
        for (let item of Object.values(data.value.functions)) {
            raw[item.scope]++;
        }
        for (let item of Object.values(data.value.attributes)) {
            raw[3 + item.scope]++;
        }
    }
    return {
        labels: ['Functions', 'Attributes'],
        datasets: [
            {
                label: "Static",
                data: [raw[0], raw[3]],
                backgroundColor: '#2080f0',
            },
            {
                label: "Class",
                data: [raw[1], raw[4]],
                backgroundColor: '#f0a020',
            },
            {
                label: "Instance",
                data: [raw[2], raw[5]],
                backgroundColor: '#d03050',
            },
        ],
    };
});
const typedEntryCounts = computed(() => {
    let raw = [0, 0, 0, 0];
    if (data.value) {
        let totalFuncs = Object.keys(data.value.functions).length;
        let totalAttrs = Object.keys(data.value.attributes).length;
        let typed = Object.values(data.value.typedEntries());
        raw[0] = typed.filter(x => x instanceof FunctionEntry).length;
        raw[1] = typed.filter(x => x instanceof AttributeEntry).length;
        raw[2] = totalFuncs - raw[0];
        raw[3] = totalAttrs - raw[1];
    }
    return {
        labels: ['Functions', 'Attributes'],
        datasets: [
            {
                label: "Typed",
                data: [raw[0], raw[1]],
                backgroundColor: '#66cc99',
            },
            {
                label: "Untyped",
                data: [raw[2], raw[3]],
                backgroundColor: '#ffcc66',
            },
        ],
    };
});
const argsEntryCounts = computed(() => {
    let raw = [0, 0, 0, 0];
    if (data.value) {
        for (let item of Object.values(data.value.functions)) {
            if (item.varKeyword() && item.varPositional()) {
                raw[3]++;
            }
            else if (item.varKeyword()) {
                raw[2]++;
            }
            else if (item.varPositional()) {
                raw[1]++;
            }
            else {
                raw[0]++;
            }
        }
    }
    return {
        labels: ['Fixed Arguments', 'Var Positional', 'Var Keyword', 'Var All'],
        datasets: [
            {
                data: raw,
                backgroundColor: ['#66ccff', '#66ff33', '#ffcc00', '#cc9933'],
            },
        ],
    };
});
</script>

<template>
    <n-flex vertical>
        <n-page-header :title="release?.toString() ?? 'Unknown'" subtitle="API Description" @back="() => router.back()">
            <template #avatar>
                <n-avatar>
                    <n-icon :component="ExtractIcon" />
                </n-avatar>
            </template>

            <template #header>
                <n-breadcrumb>
                    <HomeBreadcrumbItem />
                    <ProjectBreadcrumbItem />
                    <ReleaseBreadcrumbItem :release="release" />
                </n-breadcrumb>
            </template>

            <template #footer>
                <n-flex v-if="data" :align="'center'">
                    <MetadataViewer :data="data" />
                    <n-button-group size="small" v-if="release">
                        <ReleasePrevSuccLink :release="release" kind="extracted" />
                        <DistributionLink :release="release" />
                    </n-button-group>
                    <DistributionSwitch v-model="showDists" />
                    <StaticticsSwitch v-model="showStats" />

                    <n-tooltip>
                        <template #trigger>
                            <n-switch v-model:value="showApiLevel">
                                <template #checked>
                                    <n-icon size="large" :component="ApiLevelIcon" />
                                </template>

                                <template #unchecked>
                                    <n-icon size="large" :component="ApiLevelIcon" />
                                </template>
                            </n-switch>
                        </template>
                        API Level
                    </n-tooltip>
                    <n-tooltip>

                        <template #trigger>
                            <n-switch v-model:value="showCallgraph">
                                <template #checked>
                                    <n-icon size="large" :component="CallIcon" />
                                </template>

                                <template #unchecked>
                                    <n-icon size="large" :component="CallIcon" />
                                </template>
                            </n-switch>
                        </template>
                        Callgraph
                    </n-tooltip>
                    <n-tooltip>

                        <template #trigger>
                            <n-switch v-model:value="showInheritance">
                                <template #checked>
                                    <n-icon size="large" :component="InheritanceIcon" />
                                </template>

                                <template #unchecked>
                                    <n-icon size="large" :component="InheritanceIcon" />
                                </template>
                            </n-switch>
                        </template>
                        Inheritance
                    </n-tooltip>
                    <LogSwitchPanel :load="() => store.state.api.apiLog(release)" />
                    <CountViewer :value="Object.keys(data.publics()).length" label="Public" inline
                        :total="Object.keys(data.entriesMap()).length"></CountViewer>
                </n-flex>
            </template>
        </n-page-header>

        <NotFound v-if="error" :path="router.currentRoute.value.fullPath" size="huge"></NotFound>

        <n-spin v-else-if="!data" :size="160" style="width: 100%; margin: 50px"></n-spin>

        <n-flex v-if="data" vertical>
            <n-collapse-transition :show="showDists">
                <n-divider>
                    <n-flex :wrap="false" :align="'center'">
                        <n-icon size="large" :component="DistributionIcon" />
                        Distribution
                    </n-flex>
                </n-divider>
                <DistributionViewer :data="data.distribution" />
            </n-collapse-transition>

            <n-collapse-transition :show="showStats">
                <n-divider>
                    <n-flex :wrap="false" :align="'center'">
                        <n-icon size="large" :component="CountIcon" />
                        Statistics
                    </n-flex>
                </n-divider>
                <n-flex>
                    <DoughnutChart :chart-data="entryCounts"
                        :options="{ plugins: { legend: { position: 'bottom' }, title: { display: true, text: 'Kinds' } } }"
                        v-if="Object.keys(data.entriesMap()).length > 0" />
                    <DoughnutChart :chart-data="argsEntryCounts"
                        :options="{ plugins: { legend: { position: 'bottom' }, title: { display: true, text: 'Parameters' } } }"
                        v-if="Object.keys(data.functions).length > 0" />
                    <BarChart :chart-data="boundEntryCounts"
                        :options="{ plugins: { legend: { position: 'bottom' }, title: { display: true, text: 'Bounds' } }, scales: { x: { stacked: true }, y: { stacked: true } } }"
                        v-if="Object.keys(data.functions).length + Object.keys(data.attributes).length > 0" />
                    <BarChart :chart-data="typedEntryCounts"
                        :options="{ plugins: { legend: { position: 'bottom' }, title: { display: true, text: 'Types' } }, scales: { x: { stacked: true }, y: { stacked: true } } }"
                        v-if="Object.keys(data.functions).length + Object.keys(data.attributes).length > 0" />
                </n-flex>
            </n-collapse-transition>
            <n-tree-select filterable show-path separator="." :options="entryTreeOptions" v-model:value="currentEntryId"
                size="large" clearable placeholder="Entry ID" :render-label="(info) => renderApiTreeLabel(data!, info)"
                :filter="filterApiTreeOption" />

            <ApiEntryViewer :entry="currentEntry" v-if="currentEntry" :raw-url="data.distribution.rootPath"
                :entry-url="apiUrl(data.distribution.release)" />
        </n-flex>

        <n-modal v-model:show="showCallgraph" preset="card"
            :title="`Call Graph - ${currentEntry instanceof FunctionEntry ? currentEntry.id : 'Global'}`">

            <template #header-extra>
                <n-flex>
                    <n-switch v-model:value="showCallgraphExternal">
                        <template #checked>External</template>

                        <template #unchecked>External</template>
                    </n-switch>
                    <n-switch v-model:value="showCallgraphCallee" v-if="currentEntry instanceof FunctionEntry">

                        <template #checked>Callee</template>

                        <template #unchecked>Callee</template>
                    </n-switch>
                    <n-switch v-model:value="showCallgraphCaller" v-if="currentEntry instanceof FunctionEntry">

                        <template #checked>Caller</template>

                        <template #unchecked>Caller</template>
                    </n-switch>
                    <n-input-number v-model:value="callgraphDepth" clearable :min="0" placeholder="Depth" size="small"
                        v-if="currentEntry instanceof FunctionEntry"></n-input-number>
                </n-flex>
            </template>
            <CallgraphViewer :style="{ height: '100%' }" v-if="data && currentEntry instanceof FunctionEntry"
                :api="data" :entry="currentEntry" :depth="callgraphDepth" :caller="showCallgraphCaller"
                :callee="showCallgraphCallee" :external="showCallgraphExternal" />
            <GlobalCallgraphViewer :style="{ height: '100%' }" v-if="data && !(currentEntry instanceof FunctionEntry)"
                :api="data" :external="showCallgraphExternal"></GlobalCallgraphViewer>
        </n-modal>

        <n-modal v-model:show="showInheritance" preset="card"
            :title="`Inheritance - ${currentEntry instanceof ClassEntry ? currentEntry.id : 'Global'}`">

            <template #header-extra>
                <n-flex>
                    <n-switch v-model:value="showInheritanceExternal">
                        <template #checked>External</template>

                        <template #unchecked>External</template>
                    </n-switch>
                    <n-switch v-model:value="showInheritanceBase" v-if="(currentEntry instanceof ClassEntry)">

                        <template #checked>Base</template>

                        <template #unchecked>Base</template>
                    </n-switch>
                    <n-switch v-model:value="showInheritanceSub" v-if="(currentEntry instanceof ClassEntry)">

                        <template #checked>Subclass</template>

                        <template #unchecked>Subclass</template>
                    </n-switch>
                    <n-input-number v-model:value="inheritanceDepth" clearable :min="0" placeholder="Depth" size="small"
                        v-if="(currentEntry instanceof ClassEntry)"></n-input-number>
                </n-flex>
            </template>
            <InheritanceViewer :style="{ height: '100%' }" v-if="data && currentEntry instanceof ClassEntry" :api="data"
                :entry="currentEntry" :depth="inheritanceDepth" :subclass="showInheritanceSub"
                :base="showInheritanceBase" :external="showInheritanceExternal" />
            <GlobalInheritanceViewer :style="{ height: '100%' }" v-if="data && !(currentEntry instanceof ClassEntry)"
                :api="data" :external="showInheritanceExternal">
            </GlobalInheritanceViewer>
        </n-modal>

        <n-modal v-model:show="showApiLevel" preset="card" title="API Level">

            <template #header-extra>
                <n-flex>
                    <n-input v-model:value="apiLevelSearchPattern">
                        <template #prefix>
                            <n-icon :component="SearchIcon" />
                        </template>
                    </n-input>
                </n-flex>
            </template>
            <ApiLevelViewer v-if="data" :pattern="apiLevelSearchPattern" :api="data" :current="currentEntry">
            </ApiLevelViewer>
        </n-modal>
    </n-flex>
</template>
