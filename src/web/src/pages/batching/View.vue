<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NPageHeader, NSpace, NText, NBreadcrumb, NDrawer, NDrawerContent, NBreadcrumbItem, NSwitch, NCollapse, NCollapseItem, NLog, NIcon, NLayoutContent, NAvatar, NStatistic, NTabs, NTabPane, NCard, NButton, useOsTheme, useMessage, NDescriptions, NDescriptionsItem, NSpin } from 'naive-ui'
import { HomeIcon, RootIcon, BatchIcon, ReleaseIcon, LogIcon } from '../../components/icons'
import { useRouter, useRoute } from 'vue-router'
import HomeBreadcrumbItem from '../../components/breadcrumbs/HomeBreadcrumbItem.vue'
import ReleaseBreadcrumbItem from '../../components/breadcrumbs/ReleaseBreadcrumbItem.vue'
import { useStore } from '../../services/store'
import { Distribution, Release, ApiDescription, ProjectResult, ProducerOptions } from '../../models'
import NotFound from '../../components/NotFound.vue'
import MetadataViewer from '../../components/metadata/MetadataViewer.vue'
import BatchBreadcrumbItem from '../../components/breadcrumbs/BatchBreadcrumbItem.vue'
import DistributionViewer from '../../components/products/DistributionViewer.vue'

const store = useStore();
const router = useRouter();
const route = useRoute();
const message = useMessage();

const params = <{
    provider: string,
    id: string,
}>route.params;

const query = ProducerOptions.fromQuery(route.query);

const release = ref<string>("");
const data = ref<ProjectResult>();
const error = ref<boolean>(false);
const showlog = ref<boolean>(false);
const logcontent = ref<string>("");

onMounted(async () => {
    release.value = params.id;
    if (release.value) {
        try {
            data.value = await store.state.api.batcher.index(release.value, params.provider, query);
            query.redo = false;
        }
        catch (e) {
            console.error(e);
            error.value = true;
            message.error(`Failed to load data for ${params.id} by provider ${params.provider}.`);
        }
    }
    else {
        error.value = true;
        message.error('Invalid release ID');
    }
});

async function onLog(value: boolean) {
    if (release.value && value) {
        if (logcontent.value == "") {
            try {
                logcontent.value = await store.state.api.batcher.log(release.value, params.provider, query);
            }
            catch {
                message.error(`Failed to load log for ${params.id} by provider ${params.provider}.`);
            }
        }
    }
}
</script>

<template>
    <n-space vertical :size="20">
        <n-page-header
            :title="release?.toString() ?? 'Unknown'"
            subtitle="Batching"
            @back="() => router.back()"
        >
            <template #avatar>
                <n-avatar>
                    <n-icon>
                        <BatchIcon />
                    </n-icon>
                </n-avatar>
            </template>
            <template #header>
                <n-breadcrumb>
                    <HomeBreadcrumbItem />
                    <BatchBreadcrumbItem />
                    <n-breadcrumb-item>
                        <n-space>
                            <n-icon>
                                <ReleaseIcon />
                            </n-icon>
                            {{ release?.toString() ?? "Unknown" }}
                        </n-space>
                    </n-breadcrumb-item>
                </n-breadcrumb>
            </template>
            <template #footer>
                <n-space v-if="data">
                    <MetadataViewer :data="data" />
                    <n-switch v-model:value="showlog" @update-value="onLog">
                        <template #checked>
                            <n-icon size="large">
                                <LogIcon />
                            </n-icon>Show Log
                        </template>
                        <template #unchecked>
                            <n-icon size="large">
                                <LogIcon />
                            </n-icon>Hide Log
                        </template>
                    </n-switch>
                </n-space>
            </template>
        </n-page-header>

        <NotFound v-if="error" :path="router.currentRoute.value.fullPath"></NotFound>

        <n-spin v-else-if="!data" :size="80" style="width: 100%"></n-spin>

        <n-space vertical size="large" v-if="data">
            <n-space>
                <n-statistic :value="data.releases.length" label="Releases"></n-statistic>
                <n-statistic :value="data.preprocessed.length" label="Preprocessed">
                    <template #suffix>/ {{ data.releases.length }}</template>
                </n-statistic>
                <n-statistic :value="data.extracted.length" label="Extracted">
                    <template #suffix>/ {{ data.preprocessed.length }}</template>
                </n-statistic>
                <n-statistic :value="data.pairs.length" label="Pairs"></n-statistic>
                <n-statistic :value="data.diffed.length" label="Diffed">
                    <template #suffix>/ {{ data.pairs.length }}</template>
                </n-statistic>
                <n-statistic :value="data.evaluated.length" label="Evaluated">
                    <template #suffix>/ {{ data.diffed.length }}</template>
                </n-statistic>
                <n-statistic :value="data.reported.length" label="Reported">
                    <template #suffix>/ {{ data.evaluated.length }}</template>
                </n-statistic>
            </n-space>
            <n-collapse>
                <n-collapse-item title="Releases" name="releases">
                    <n-space>
                        <span
                            v-for="item in data.releases"
                            :key="item.toString()"
                        >{{ item.toString() }}</span>
                    </n-space>
                </n-collapse-item>
                <n-collapse-item title="Preprocessed" name="preprocessed">
                    <n-space>
                        <n-button
                            v-for="item in data.preprocessed"
                            :key="item.toString()"
                            text
                            tag="a"
                            :href="`/preprocessing/${params.provider}/${item.toString()}/`"
                            target="_blank"
                            type="primary"
                        >{{ item.toString() }}</n-button>
                    </n-space>
                </n-collapse-item>
                <n-collapse-item title="Extracted" name="extracted">
                    <n-space>
                        <n-button
                            v-for="item in data.extracted"
                            :key="item.toString()"
                            text
                            tag="a"
                            :href="`/extracting/${params.provider}/${item.toString()}/`"
                            target="_blank"
                            type="primary"
                        >{{ item.toString() }}</n-button>
                    </n-space>
                </n-collapse-item>
                <n-collapse-item title="Pairs" name="pairs">
                    <n-space>
                        <span
                            v-for="item in data.pairs"
                            :key="item.toString()"
                        >{{ item.toString() }}</span>
                    </n-space>
                </n-collapse-item>
                <n-collapse-item title="Diffed" name="diffed">
                    <n-space>
                        <n-button
                            v-for="item in data.diffed"
                            :key="item.toString()"
                            text
                            tag="a"
                            :href="`/differing/${params.provider}/${item.toString()}/`"
                            target="_blank"
                            type="primary"
                        >{{ item.toString() }}</n-button>
                    </n-space>
                </n-collapse-item>
                <n-collapse-item title="Evaluated" name="evaluated">
                    <n-space>
                        <n-button
                            v-for="item in data.evaluated"
                            :key="item.toString()"
                            text
                            tag="a"
                            :href="`/evaluating/${params.provider}/${item.toString()}/`"
                            target="_blank"
                            type="primary"
                        >{{ item.toString() }}</n-button>
                    </n-space>
                </n-collapse-item>
                <n-collapse-item title="Reported" name="reported">
                    <n-space>
                        <n-button
                            v-for="item in data.reported"
                            :key="item.toString()"
                            text
                            tag="a"
                            :href="`/reporting/${params.provider}/${item.toString()}/`"
                            target="_blank"
                            type="primary"
                        >{{ item.toString() }}</n-button>
                    </n-space>
                </n-collapse-item>
            </n-collapse>
        </n-space>

        <n-drawer v-model:show="showlog" :width="600" placement="right" v-if="data">
            <n-drawer-content title="Log" :native-scrollbar="false">
                <n-log :log="logcontent" :rows="50" language="log"></n-log>
            </n-drawer-content>
        </n-drawer>
    </n-space>
</template>
