<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NPageHeader, NSpace, NText, NBreadcrumb, NDrawer, NDrawerContent, NSwitch, NLog, NIcon, NLayoutContent, NAvatar, NStatistic, NTabs, NTabPane, NCard, NButton, useOsTheme, useMessage, NDescriptions, NDescriptionsItem, NSpin } from 'naive-ui'
import { HomeIcon, RootIcon, ExtractIcon, LogIcon } from '../../components/icons'
import { useRouter, useRoute } from 'vue-router'
import HomeBreadcrumbItem from '../../components/breadcrumbs/HomeBreadcrumbItem.vue'
import PreprocessBreadcrumbItem from '../../components/breadcrumbs/PreprocessBreadcrumbItem.vue'
import ReleaseBreadcrumbItem from '../../components/breadcrumbs/ReleaseBreadcrumbItem.vue'
import { useStore } from '../../services/store'
import { Distribution, Release, ApiDescription } from '../../models'
import NotFound from '../../components/NotFound.vue'
import MetadataViewer from '../../components/metadata/MetadataViewer.vue'
import ExtractBreadcrumbItem from '../../components/breadcrumbs/ExtractBreadcrumbItem.vue'
import DistributionViewer from '../../components/metadata/DistributionViewer.vue'

const store = useStore();
const router = useRouter();
const route = useRoute();
const message = useMessage();

const params = <{
    provider: string,
    id: string,
}>route.params;

const release = ref<Release>();
const data = ref<ApiDescription>();
const error = ref<boolean>(false);
const showlog = ref<boolean>(false);
const logcontent = ref<string>("");

onMounted(async () => {
    release.value = Release.fromString(params.id);
    if (release.value) {
        try {
            data.value = await store.state.api.extractor.process(release.value, params.provider);
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
});

async function onLog(value: boolean) {
    if (release.value && value) {
        if (logcontent.value == "") {
            try {
                logcontent.value = await store.state.api.preprocessor.log(release.value, params.provider);
            }
            catch {
                message.error(`Failed to load log for ${params.id} by provider ${params.provider}.`);
            }
        }
    }
}
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

        <n-space vertical size="large">
            <DistributionViewer v-if="data?.distribution" :data="data.distribution" />

            <n-descriptions title="API Information" v-if="data">
                <n-descriptions-item>
                    <template #label>Entries</template>
                    {{ Object.keys(data.entries).length }}
                </n-descriptions-item>
                <n-descriptions-item>
                    <template #label>Modules</template>
                    {{ Object.keys(data.modules()).length }}
                </n-descriptions-item>
                <n-descriptions-item>
                    <template #label>Classes</template>
                    {{ Object.keys(data.classes()).length }}
                </n-descriptions-item>
                <n-descriptions-item>
                    <template #label>Functions</template>
                    {{ Object.keys(data.funcs()).length }}
                </n-descriptions-item>
                <n-descriptions-item>
                    <template #label>Attributes</template>
                    {{ Object.keys(data.attrs()).length }}
                </n-descriptions-item>
            </n-descriptions>
        </n-space>

        <n-drawer v-model:show="showlog" :width="600" placement="right" v-if="data">
            <n-drawer-content title="Log" :native-scrollbar="false">
                <n-log :log="logcontent" :rows="50"></n-log>
            </n-drawer-content>
        </n-drawer>
    </n-space>
</template>
