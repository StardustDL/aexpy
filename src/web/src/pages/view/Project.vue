<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NPageHeader, NFlex, NSpace, NText, NBreadcrumb, NCollapseTransition, NDivider, NTooltip, NProgress, NBreadcrumbItem, NSwitch, NCollapse, useLoadingBar, NCollapseItem, NLog, NIcon, NLayoutContent, NAvatar, NStatistic, NTabs, NTabPane, NCard, NButton, useOsTheme, useMessage, NDescriptions, NDescriptionsItem, NSpin } from 'naive-ui'
import { HomeIcon, RootIcon, DataIcon, TrendIcon, CountIcon, PackageIcon, LogIcon, PreprocessIcon, VersionIcon, DiffIcon, ExtractIcon, EvaluateIcon, ReportIcon } from '../../components/icons'
import { useRouter, useRoute } from 'vue-router'
import HomeBreadcrumbItem from '../../components/breadcrumbs/HomeBreadcrumbItem.vue'
import { useStore } from '../../services/store'
import { Distribution, Release, ApiDescription, ApiDifference, Report, ReleasePair, ProduceState, ProjectProductIndex } from '../../models'
import { numberSum, numberAverage, publicVars, apiUrl, changeUrl, distributionUrl, reportUrl, hashedColor } from '../../services/utils'
import NotFound from '../../components/NotFound.vue'
import ProjectBreadcrumbItem from '../../components/breadcrumbs/ProjectBreadcrumbItem.vue'
import CountViewer from '../../components/metadata/CountViewer.vue'
import { LineChart } from 'vue-chart-3'
import { BreakingRank, getRankColor } from '../../models/difference'
import { AttributeEntry, FunctionEntry, getTypeColor } from '../../models/description'
import ProjectTrendViewer from '../../components/products/ProjectTrendViewer.vue'
import ProjectStatsViewer from '../../components/products/ProjectStatsViewer.vue'
import LogSwitchPanel from '../../components/switches/LogSwitchPanel.vue'
import StaticticsSwitch from '../../components/switches/StatisticsSwitch.vue'

const props = defineProps<{ project: string }>();

const store = useStore();
const router = useRouter();
const message = useMessage();
const loadingbar = useLoadingBar();

const showTrends = ref<boolean>(false);
const showStats = ref<boolean>(false);

const data = ref<ProjectProductIndex>();
const error = ref<boolean>(false);

onMounted(async () => {
    loadingbar.start();
    try {
        data.value = await store.state.api.package(props.project).index();
        publicVars({ "data": data.value });
        loadingbar.finish();
    }
    catch (e) {
        console.error(e);
        error.value = true;
        loadingbar.error();
        message.error(`Failed to load data for ${props.project}.`);
    }
});

</script>

<template>
    <n-flex vertical>
        <n-page-header :title="project ?? 'Unknown'" subtitle="Projects" @back="() => router.back()">
            <template #avatar>
                <n-avatar>
                    <n-icon :component="PackageIcon" />
                </n-avatar>
            </template>

            <template #header>
                <n-breadcrumb>
                    <HomeBreadcrumbItem />
                    <ProjectBreadcrumbItem />
                    <n-breadcrumb-item>
                        <router-link to="#">
                            <n-icon :component="PackageIcon" />
                            {{ props.project ?? "Unknown" }}
                        </router-link>
                    </n-breadcrumb-item>
                </n-breadcrumb>
            </template>

            <template #footer>
                <n-flex v-if="data">
                    <StaticticsSwitch v-model="showStats" />
                    <n-tooltip>
                        <template #trigger>
                            <n-switch v-model:value="showTrends">
                                <template #checked>
                                    <n-icon size="large" :component="TrendIcon" />
                                </template>

                                <template #unchecked>
                                    <n-icon size="large" :component="TrendIcon" />
                                </template>
                            </n-switch>
                        </template>
                        Trends (may cost much time & traffic)
                    </n-tooltip>
                    <LogSwitchPanel :load="async () => ''" />
                </n-flex>
            </template>
        </n-page-header>

        <NotFound v-if="error" :path="router.currentRoute.value.fullPath" size="huge"></NotFound>

        <n-spin v-else-if="!data" :size="160" style="width: 100%; margin: 50px"></n-spin>

        <n-flex vertical size="large" v-if="data">
            <n-collapse-transition :show="showStats">
                <n-divider>
                    <n-flex :wrap="false" :align="'center'">
                        <n-icon size="large" :component="CountIcon" />
                        Statistics
                    </n-flex>
                </n-divider>
                <ProjectStatsViewer :data="data" v-if="showStats" />
            </n-collapse-transition>
            <n-collapse-transition :show="showTrends">
                <n-divider>
                    <n-flex :wrap="false" :align="'center'">
                        <n-icon size="large" :component="TrendIcon" />
                        Trends
                    </n-flex>
                </n-divider>
                <ProjectTrendViewer :data="data" v-if="showTrends" />
            </n-collapse-transition>

            <n-divider>
                <n-flex :wrap="false" :align="'center'">
                    <n-icon size="large" :component="DataIcon" />
                    Data
                </n-flex>
            </n-divider>

            <n-collapse>
                <n-collapse-item name="releases">

                    <template #header>
                        <n-flex :align="'center'">
                            <n-icon size="large" :component="PackageIcon" />
                            Releases
                            <n-text>{{ data.releases.length }}</n-text>
                        </n-flex>
                    </template>
                    <n-space>
                        <n-button v-for="item in data.releases" :key="item.toString()" text tag="a"
                            :href="`https://pypi.org/project/${item.project}/${item.version}/`" target="_blank">{{
            item.toString()
        }}</n-button>
                    </n-space>
                </n-collapse-item>
                <n-collapse-item title="Preprocessed" name="preprocessed">

                    <template #header>
                        <n-flex :align="'center'">
                            <n-icon size="large" :component="PreprocessIcon" />
                            Preprocessed
                            <CountViewer :value="data.preprocessed.length" inline :total="data.releases.length" />
                        </n-flex>
                    </template>
                    <n-space>
                        <router-link :to="distributionUrl(item)" v-for="item in data.releases" :key="item.toString()"
                            custom v-slot="{ href, navigate }">
                            <n-button text tag="a" :href="href" @click="navigate"
                                :type="data.ispreprocessed(item) ? 'success' : 'error'">{{
            item.toString()
        }}</n-button>
                        </router-link>
                    </n-space>
                </n-collapse-item>
                <n-collapse-item name="extracted">

                    <template #header>
                        <n-flex :align="'center'">
                            <n-icon size="large" :component="ExtractIcon" />
                            Extracted
                            <CountViewer :value="data.extracted.length" inline :total="data.preprocessed.length" />
                        </n-flex>
                    </template>
                    <n-space>
                        <router-link :to="apiUrl(item)" v-for="item in data.preprocessed" :key="item.toString()" custom
                            v-slot="{ href, navigate }">
                            <n-button text tag="a" :href="href" @click="navigate"
                                :type="data.isextracted(item) ? 'success' : 'error'">{{
            item.toString() }}</n-button>
                        </router-link>
                    </n-space>
                </n-collapse-item>
                <n-collapse-item name="pairs">

                    <template #header>
                        <n-flex :align="'center'">
                            <n-icon size="large" :component="VersionIcon" />
                            Pairs
                            <n-text>{{ data.pairs.length }}</n-text>
                        </n-flex>
                    </template>
                    <n-space>
                        <n-button v-for="item in data.pairs" :key="item.toString()" text tag="a">{{
            item.toString()
        }}</n-button>
                    </n-space>
                </n-collapse-item>
                <n-collapse-item name="diffed">

                    <template #header>
                        <n-flex :align="'center'">
                            <n-icon size="large" :component="DiffIcon" />
                            Diffed
                            <CountViewer :value="data.diffed.length" inline :total="data.pairs.length" />
                        </n-flex>
                    </template>
                    <n-space>
                        <router-link :to="changeUrl(item)" v-for="item in data.pairs" :key="item.toString()" custom
                            v-slot="{ href, navigate }">
                            <n-button text tag="a" :href="href" @click="navigate"
                                :type="data.isdiffed(item) ? 'success' : 'error'">{{
            item.toString() }}</n-button>
                        </router-link>
                    </n-space>
                </n-collapse-item>
                <n-collapse-item name="reported">

                    <template #header>
                        <n-flex :align="'center'">
                            <n-icon size="large" :component="ReportIcon" />
                            Reported
                            <CountViewer :value="data.reported.length" inline :total="data.diffed.length" />
                        </n-flex>
                    </template>
                    <n-space>
                        <router-link :to="reportUrl(item)" v-for="item in data.diffed" :key="item.toString()" custom
                            v-slot="{ href, navigate }">
                            <n-button text tag="a" :href="href" @click="navigate"
                                :type="data.isreported(item) ? 'success' : 'error'">{{
                                item.toString() }}</n-button>
                        </router-link>
                    </n-space>
                </n-collapse-item>
            </n-collapse>
        </n-flex>
    </n-flex>
</template>
