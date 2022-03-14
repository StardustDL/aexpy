<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NPageHeader, NSpace, SelectOption, NText, NSelect, NButtonGroup, NDivider, NBreadcrumb, NAutoComplete, NDrawer, NDrawerContent, NCollapseTransition, useLoadingBar, NSwitch, NLog, NIcon, NLayoutContent, NAvatar, NStatistic, NTabs, NTabPane, NCard, NButton, useOsTheme, useMessage, NDescriptions, NDescriptionsItem, NSpin } from 'naive-ui'
import { HomeIcon, RootIcon, PreprocessIcon, CountIcon, ExtractIcon, LogIcon, ReleaseIcon } from '../../components/icons'
import { useRouter, useRoute } from 'vue-router'
import HomeBreadcrumbItem from '../../components/breadcrumbs/HomeBreadcrumbItem.vue'
import PreprocessBreadcrumbItem from '../../components/breadcrumbs/PreprocessBreadcrumbItem.vue'
import ReleaseBreadcrumbItem from '../../components/breadcrumbs/ReleaseBreadcrumbItem.vue'
import { useStore } from '../../services/store'
import { Distribution, Release, ApiDescription, ProducerOptions } from '../../models'
import NotFound from '../../components/NotFound.vue'
import MetadataViewer from '../../components/metadata/MetadataViewer.vue'
import ExtractBreadcrumbItem from '../../components/breadcrumbs/ExtractBreadcrumbItem.vue'
import DistributionViewer from '../../components/products/DistributionViewer.vue'
import ApiEntryViewer from '../../components/entries/ApiEntryViewer.vue'
import CountViewer from '../../components/metadata/CountViewer.vue'
import { DoughnutChart } from 'vue-chart-3';
import { AttributeEntry, ClassEntry, FunctionEntry, ModuleEntry } from '../../models/description'
import ProviderLinker from '../../components/metadata/ProviderLinker.vue'

const store = useStore();
const router = useRouter();
const route = useRoute();
const message = useMessage();
const loadingbar = useLoadingBar();

const params = <{
    provider: string,
    id: string,
}>route.params;

const showDists = ref<boolean>(false);
const showStats = ref<boolean>(true);

const query = ProducerOptions.fromQuery(route.query);

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
            data.value = await store.state.api.extractor.process(release.value, params.provider, query);
            query.redo = false;

            if (data.value.distribution.topModules.length > 0) {
                let topModule = data.value.distribution.topModules[0];
                if (data.value.entries[topModule] != undefined) {
                    currentEntry.value = topModule;
                }
            }
        }
        catch (e) {
            console.error(e);
            error.value = true;
            message.error(`Failed to load extracted data for ${params.id} by provider ${params.provider}.`);
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
                logcontent.value = await store.state.api.extractor.log(release.value, params.provider, query);
            }
            catch {
                message.error(`Failed to load log for ${params.id} by provider ${params.provider}.`);
            }
        }
    }
}

const currentEntry = ref<string>("");
const entryOptions = computed(() => {
    if (!data.value) {
        return [];
    }
    let rawdata = data.value;
    let keys = Object.keys(rawdata.entries).filter(key => ~key.indexOf(currentEntry.value));
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
    let raw = [0, 0, 0, 0];
    if (data.value) {
        raw = [Object.keys(data.value.modules()).length, Object.keys(data.value.classes()).length, Object.keys(data.value.funcs()).length, Object.keys(data.value.attrs()).length];
    }
    return {
        labels: ['Modules', 'Classes', 'Functions', 'Attributes'],
        datasets: [
            {
                data: raw,
                backgroundColor: ['#2080f0', '#f0a020', '#18a058', '#d03050'],
            },
        ],
    };
});
const boundEntryCounts = computed(() => {
    let raw = [0, 0, 0, 0];
    if (data.value) {
        for (let item of Object.values(data.value.funcs())) {
            if (item.bound) {
                raw[0]++;
            }
            else {
                raw[2]++;
            }
        }
        for (let item of Object.values(data.value.attrs())) {
            if (item.bound) {
                raw[1]++;
            }
            else {
                raw[3]++;
            }
        }
    }
    return {
        labels: ['Bound Functions', 'Bound Attributes', 'Unbound Functions', 'Unbound Attributes'],
        datasets: [
            {
                data: raw,
                backgroundColor: ['#66ff66', '#ffcc66', '#66cc99', '#ff3300'],
            }
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
        <n-page-header
            :title="release?.toString() ?? 'Unknown'"
            subtitle="Extracting"
            @back="() => router.back()"
        >
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
                    <ExtractBreadcrumbItem />
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
                    <n-button-group size="small" v-if="release">
                        <n-button
                            tag="a"
                            :href="`/preprocessing/${params.provider}/${release.toString()}/`"
                            target="_blank"
                            type="info"
                            ghost
                        >
                            <n-icon size="large">
                                <PreprocessIcon />
                            </n-icon>
                        </n-button>
                    </n-button-group>
                    <ProviderLinker />
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
                    <CountViewer :value="Object.keys(data.entries).length" label="Entries"></CountViewer>
                    <DoughnutChart
                        :chart-data="entryCounts"
                        :options="{ plugins: { legend: { position: 'bottom' }, title: { display: true, text: 'Kinds' } } }"
                        v-if="Object.keys(data.entries).length > 0"
                    />
                    <DoughnutChart
                        :chart-data="boundEntryCounts"
                        :options="{ plugins: { legend: { position: 'bottom' }, title: { display: true, text: 'Bounds' } } }"
                        v-if="Object.keys(data.funcs()).length + Object.keys(data.attrs()).length > 0"
                    />
                    <DoughnutChart
                        :chart-data="argsEntryCounts"
                        :options="{ plugins: { legend: { position: 'bottom' }, title: { display: true, text: 'Parameters' } } }"
                        v-if="Object.keys(data.funcs()).length > 0"
                    />
                </n-space>
            </n-collapse-transition>
            <n-divider>Entries</n-divider>
            <n-auto-complete
                v-model:value="currentEntry"
                :options="entryOptions"
                size="large"
                clearable
                placeholder="Entry ID"
            />
            
            <ApiEntryViewer
                :entry="data.entries[currentEntry]"
                v-if="data.entries[currentEntry]"
                :raw-url="data.distribution.wheelDir"
            />
        </n-space>

        <n-drawer v-model:show="showlog" :width="600" placement="right" v-if="data">
            <n-drawer-content title="Log" :native-scrollbar="false">
                <n-spin v-if="logcontent == undefined" :size="60" style="width: 100%"></n-spin>
                <n-log v-else :log="logcontent" :rows="40" language="log"></n-log>
            </n-drawer-content>
        </n-drawer>
    </n-space>
</template>
