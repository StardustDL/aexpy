<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NPageHeader, NSpace, NButtonGroup, NDivider, NInputNumber, NBreadcrumb, NAutoComplete, NModal, NDrawer, NDrawerContent, NCollapseTransition, useLoadingBar, NSwitch, NLog, NIcon, NLayoutContent, NAvatar, NStatistic, NTabs, NTabPane, NCard, NButton, useOsTheme, useMessage, NDescriptions, NDescriptionsItem, NSpin } from 'naive-ui'
import { CallIcon, PreprocessIcon, CountIcon, ExtractIcon, LogIcon, ReleaseIcon } from '../../components/icons'
import { useRouter, useRoute } from 'vue-router'
import CallgraphViewer from '../../components/entries/CallgraphViewer.vue';
import HomeBreadcrumbItem from '../../components/breadcrumbs/HomeBreadcrumbItem.vue'
import ReleaseBreadcrumbItem from '../../components/breadcrumbs/ReleaseBreadcrumbItem.vue'
import { useStore } from '../../services/store'
import { Release, ApiDescription, ProduceMode } from '../../models'
import NotFound from '../../components/NotFound.vue'
import MetadataViewer from '../../components/metadata/MetadataViewer.vue'
import DescriptionBreadcrumbItem from '../../components/breadcrumbs/DescriptionBreadcrumbItem.vue'
import DistributionViewer from '../../components/products/DistributionViewer.vue'
import ApiEntryViewer from '../../components/entries/ApiEntryViewer.vue'
import CountViewer from '../../components/metadata/CountViewer.vue'
import { DoughnutChart, BarChart } from 'vue-chart-3';
import { AttributeEntry, ClassEntry, FunctionEntry, ModuleEntry } from '../../models/description'
import { publicVars } from '../../services/utils'
import GlobalCallgraphViewer from '../../components/entries/GlobalCallgraphViewer.vue';

const store = useStore();
const router = useRouter();
const route = useRoute();
const message = useMessage();
const loadingbar = useLoadingBar();

const params = route.params as {
    id: string,
};

const showDists = ref<boolean>(false);
const showStats = ref<boolean>(true);
const showCallgraph = ref<boolean>(false);
const showCallgraphCallee = ref<boolean>(true);
const showCallgraphCaller = ref<boolean>(true);
const showCallgraphExternal = ref<boolean>(true);
const callgraphDepth = ref<number>(2);

let mode: ProduceMode = parseInt(route.query.mode?.toString() ?? ProduceMode.Access.toString()) as ProduceMode;

const release = ref<Release>();
const data = ref<ApiDescription>();
const error = ref<boolean>(false);
const showlog = ref<boolean>(false);
const logcontent = ref<string>();

onMounted(async () => {
    loadingbar.start();
    release.value = Release.fromString(params.id);
    if (release.value) {
        try {
            data.value = await store.state.api.api(release.value);
            release.value = data.value.distribution.release;
            publicVars({ "data": data.value });
            mode = ProduceMode.Access;

            if (route.query.entry != undefined) {
                currentEntryId.value = route.query.entry.toString();
                showStats.value = false;
            }
            else {
                if (data.value.distribution.topModules.length > 0) {
                    let topModule = data.value.distribution.topModules[0];
                    if (data.value.entries[topModule] != undefined) {
                        currentEntryId.value = topModule;
                    }
                }
            }
        }
        catch (e) {
            console.error(e);
            error.value = true;
            message.error(`Failed to load extracted data for ${params.id}.`);
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
                logcontent.value = await store.state.api.apiLog(release.value);
                publicVars({ "log": logcontent.value });
            }
            catch {
                message.error(`Failed to load log for ${params.id}.`);
            }
        }
    }
}

const currentEntryId = ref<string>("");
const currentEntry = computed(() => data.value?.entries[currentEntryId.value]);
const entryOptions = computed(() => {
    if (!data.value) {
        return [];
    }
    let rawdata = data.value;
    let entries = rawdata.entries;
    let text = currentEntryId.value;
    if (currentEntryId.value.startsWith("M:")) {
        entries = rawdata.modules();
        text = currentEntryId.value.substring(2);
    }
    else if (currentEntryId.value.startsWith("C:")) {
        entries = rawdata.classes();
        text = currentEntryId.value.substring(2);
    }
    else if (currentEntryId.value.startsWith("F:")) {
        entries = rawdata.funcs();
        text = currentEntryId.value.substring(2);
    }
    else if (currentEntryId.value.startsWith("A:")) {
        entries = rawdata.attrs();
        text = currentEntryId.value.substring(2);
    }
    let keys = Object.keys(entries).filter(key => ~key.indexOf(text.trim()));
    let modules = [];
    let classes = [];
    let funcs = [];
    let attrs = [];
    for (let key of keys) {
        let value = rawdata.entries[key];
        if (value instanceof ModuleEntry) {
            modules.push(key);
        }
        else if (value instanceof ClassEntry) {
            classes.push(key);
        }
        else if (value instanceof FunctionEntry) {
            funcs.push(key);
        }
        else if (value instanceof AttributeEntry) {
            attrs.push(key);
        }
    }
    let ret = [];
    if (modules.length > 0) {
        ret.push({
            type: "group",
            label: "Modules",
            key: "Modules",
            children: modules
        });
    }
    if (classes.length > 0) {
        ret.push({
            type: "group",
            label: "Classes",
            key: "Classes",
            children: classes
        });
    }
    if (funcs.length > 0) {
        ret.push({
            type: "group",
            label: "Functions",
            key: "Functions",
            children: funcs
        });
    }
    if (attrs.length > 0) {
        ret.push({
            type: "group",
            label: "Attributes",
            key: "Attributes",
            children: attrs
        });
    }
    return ret;
});

const entryCounts = computed(() => {
    let raw: { label: string, data: number, backgroundColor: string }[] = [];
    if (data.value) {
        let modules = Object.values(data.value.modules());
        let classes = Object.values(data.value.classes());
        let funcs = Object.values(data.value.funcs());
        let attrs = Object.values(data.value.attrs());

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
        for (let item of Object.values(data.value.funcs())) {
            raw[item.scope]++;
        }
        for (let item of Object.values(data.value.attrs())) {
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
        let totalFuncs = Object.keys(data.value.funcs()).length;
        let totalAttrs = Object.keys(data.value.attrs()).length;
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
        for (let item of Object.values(data.value.funcs())) {
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
    <n-space vertical>
        <n-page-header :title="release?.toString() ?? 'Unknown'" subtitle="API Description" @back="() => router.back()">
            <template #avatar>
                <n-avatar>
                    <n-icon>
                        <ExtractIcon />
                    </n-icon>
                </n-avatar>
            </template>
            <template #header>
                <n-breadcrumb>
                    <HomeBreadcrumbItem />
                    <DescriptionBreadcrumbItem />
                    <ReleaseBreadcrumbItem :release="release" />
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
                    <n-switch v-model:value="showDists">
                        <template #checked>
                            <n-icon size="large">
                                <ReleaseIcon />
                            </n-icon>
                        </template>
                        <template #unchecked>
                            <n-icon size="large">
                                <ReleaseIcon />
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
                    <n-switch v-model:value="showCallgraph" v-if="data">
                        <template #checked>
                            <n-icon size="large">
                                <CallIcon />
                            </n-icon>
                        </template>
                        <template #unchecked>
                            <n-icon size="large">
                                <CallIcon />
                            </n-icon>
                        </template>
                    </n-switch>
                    <n-button-group size="small" v-if="release">
                        <n-button tag="a" :href="`/distributions/${release.toString()}/`"
                            target="_blank" type="info" ghost>
                            <n-icon size="large">
                                <PreprocessIcon />
                            </n-icon>
                        </n-button>
                    </n-button-group>
                </n-space>
            </template>
        </n-page-header>

        <NotFound v-if="error" :path="router.currentRoute.value.fullPath"></NotFound>

        <n-spin v-else-if="!data" :size="80" style="width: 100%"></n-spin>

        <n-space v-if="data" vertical>
            <n-collapse-transition :show="showDists">
                <n-divider>Distribution</n-divider>
                <DistributionViewer :data="data.distribution" />
            </n-collapse-transition>

            <n-collapse-transition :show="showStats">
                <n-divider>Statistics</n-divider>
                <n-space>
                    <n-space vertical>
                        <CountViewer :value="Object.keys(data.publics()).length" label="Public"
                            :total="Object.keys(data.entries).length"></CountViewer>
                        <CountViewer :value="Object.keys(data.privates()).length" label="Private"
                            :total="Object.keys(data.entries).length"></CountViewer>
                    </n-space>
                    <DoughnutChart :chart-data="entryCounts"
                        :options="{ plugins: { legend: { position: 'bottom' }, title: { display: true, text: 'Kinds' } } }"
                        v-if="Object.keys(data.entries).length > 0" />
                    <DoughnutChart :chart-data="argsEntryCounts"
                        :options="{ plugins: { legend: { position: 'bottom' }, title: { display: true, text: 'Parameters' } } }"
                        v-if="Object.keys(data.funcs()).length > 0" />
                    <BarChart :chart-data="boundEntryCounts"
                        :options="{ plugins: { legend: { position: 'bottom' }, title: { display: true, text: 'Bounds' } }, scales: { x: { stacked: true }, y: { stacked: true } } }"
                        v-if="Object.keys(data.funcs()).length + Object.keys(data.attrs()).length > 0" />
                    <BarChart :chart-data="typedEntryCounts"
                        :options="{ plugins: { legend: { position: 'bottom' }, title: { display: true, text: 'Types' } }, scales: { x: { stacked: true }, y: { stacked: true } } }"
                        v-if="Object.keys(data.funcs()).length + Object.keys(data.attrs()).length > 0" />
                </n-space>
            </n-collapse-transition>
            <n-divider>Entries</n-divider>
            <n-auto-complete v-model:value="currentEntryId" :options="entryOptions" size="large" clearable
                placeholder="Entry ID" />

            <ApiEntryViewer :entry="currentEntry" v-if="currentEntry" :raw-url="data.distribution.rootPath"
                :entry-url="`/apis/${params.id}/`" />
        </n-space>

        <n-modal v-model:show="showCallgraph" preset="card"
            :title="`Call Graph - ${currentEntry instanceof FunctionEntry ? currentEntry.id : 'Global'}`">
            <template #header-extra>
                <n-space>
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
                </n-space>
            </template>
            <CallgraphViewer :style="{ height: '100%' }" v-if="data && currentEntry instanceof FunctionEntry"
                :api="data" :entry="currentEntry" :entry-url="`/apis/${params.id}/`"
                :depth="callgraphDepth" :caller="showCallgraphCaller" :callee="showCallgraphCallee"
                :external="showCallgraphExternal" />
            <GlobalCallgraphViewer :style="{ height: '100%' }" v-if="data && !(currentEntry instanceof FunctionEntry)"
                :api="data" :entry-url="`/apis/${params.id}/`"
                :external="showCallgraphExternal"></GlobalCallgraphViewer>
        </n-modal>

        <n-drawer v-model:show="showlog" :width="600" placement="right" v-if="data">
            <n-drawer-content title="Log" :native-scrollbar="false">
                <n-spin v-if="logcontent == undefined" :size="60" style="width: 100%"></n-spin>
                <n-log v-else :log="logcontent" :rows="40" language="log"></n-log>
            </n-drawer-content>
        </n-drawer>
    </n-space>
</template>
