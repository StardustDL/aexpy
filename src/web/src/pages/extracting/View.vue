<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NPageHeader, NSpace, SelectOption, NText, NSelect, NButtonGroup, NBreadcrumb, NDrawer, NDrawerContent, NCollapseTransition, useLoadingBar, NSwitch, NLog, NIcon, NLayoutContent, NAvatar, NStatistic, NTabs, NTabPane, NCard, NButton, useOsTheme, useMessage, NDescriptions, NDescriptionsItem, NSpin } from 'naive-ui'
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
const showCounts = ref<boolean>(true);

const query = ProducerOptions.fromQuery(route.query);

const release = ref<Release>();
const data = ref<ApiDescription>();
const error = ref<boolean>(false);
const showlog = ref<boolean>(false);
const logcontent = ref<string>("");

onMounted(async () => {
    loadingbar.start();
    release.value = Release.fromString(params.id);
    if (release.value) {
        try {
            data.value = await store.state.api.extractor.process(release.value, params.provider, query);
            query.redo = false;
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
        if (logcontent.value == "") {
            try {
                logcontent.value = await store.state.api.extractor.log(release.value, params.provider, query);
            }
            catch {
                message.error(`Failed to load log for ${params.id} by provider ${params.provider}.`);
            }
        }
    }
}

const rawoptions = computed(() => {
    if (data.value) {
        let entries = data.value.entries;
        return Object.keys(entries).map(key => {
            return {
                label: `${entries[key].getType()}: ${key}`,
                value: key
            }
        });
    }
    return [];
});

const loadingEntry = ref<boolean>(false);
const options = ref<SelectOption[]>([]);
const currentEntry = ref<string>("");

async function onSearch(query: string) {
    if (!query.length) {
        options.value = rawoptions.value;
        return;
    }
    loadingEntry.value = true;
    let values = rawoptions.value.filter(
        (item) =>
            ~item.label.indexOf(query)
    )
    if (loadingEntry.value != true) {
        return;
    }
    options.value = values;
    loadingEntry.value = false;
}

</script>

<template>
    <n-space vertical :size="20">
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
                    <n-switch v-model:value="showCounts">
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
                </n-space>
            </template>
        </n-page-header>

        <NotFound v-if="error" :path="router.currentRoute.value.fullPath"></NotFound>

        <n-spin v-else-if="!data" :size="80" style="width: 100%"></n-spin>

        <n-collapse-transition :show="showDists" v-if="data">
            <DistributionViewer :data="data.distribution" />
        </n-collapse-transition>

        <n-collapse-transition :show="showCounts" v-if="data">
            <n-space>
                <CountViewer label="Modules" :value="Object.keys(data.modules()).length" :total="Object.keys(data.entries).length"></CountViewer>
                <CountViewer label="Classes" :value="Object.keys(data.classes()).length" :total="Object.keys(data.entries).length"></CountViewer>
                <CountViewer label="Functions" :value="Object.keys(data.funcs()).length" :total="Object.keys(data.entries).length"></CountViewer>
                <CountViewer label="Attributes" :value="Object.keys(data.attrs()).length" :total="Object.keys(data.entries).length"></CountViewer>
            </n-space>
        </n-collapse-transition>

        <n-space v-if="data" vertical>
            <n-select
                v-model:value="currentEntry"
                :options="options"
                filterable
                :loading="loadingEntry"
                clearable
                remote
                size="large"
                @search="onSearch"
            ></n-select>

            <ApiEntryViewer :entry="data.entries[currentEntry]" v-if="data.entries[currentEntry]" />
        </n-space>

        <n-drawer v-model:show="showlog" :width="600" placement="right" v-if="data">
            <n-drawer-content title="Log" :native-scrollbar="false">
                <n-log :log="logcontent" :rows="40" language="log"></n-log>
            </n-drawer-content>
        </n-drawer>
    </n-space>
</template>
