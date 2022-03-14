<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { NPageHeader, NSpace, NText, NSwitch, NBreadcrumb, NIcon, NLayoutContent, NAvatar, NStatistic, NTabs, NTabPane, NCard, NButton, useOsTheme, NInput, NInputGroup } from 'naive-ui'
import { HomeIcon, RootIcon, CodeIcon, GoIcon, ProviderIcon, ReleaseIcon } from '../../components/icons'
import { useRouter } from 'vue-router'
import HomeBreadcrumbItem from '../../components/breadcrumbs/HomeBreadcrumbItem.vue'
import CodeBreadcrumbItem from '../../components/breadcrumbs/CodeBreadcrumbItem.vue'
import { useStore } from '../../services/store'
import { ProducerOptions, Provider, Release, ReleasePair } from '../../models'
import ProducerOptionsSetter from '../../components/metadata/ProducerOptionsSetter.vue'
import ReleasePairSetter from '../../components/metadata/ReleasePairSetter.vue'
import ProviderSetter from '../../components/metadata/ProviderSetter.vue'

const store = useStore();
const router = useRouter();

const editor = ref();
let runtime = <any>undefined;
let main = <any>undefined;

</script>

<template>
    <n-space vertical>
        <n-page-header title="Coding" subtitle="Aexpy" @back="() => router.back()">
            <template #avatar>
                <n-avatar>
                    <n-icon>
                        <CodeIcon />
                    </n-icon>
                </n-avatar>
            </template>
            <template #header>
                <n-breadcrumb>
                    <HomeBreadcrumbItem />
                    <CodeBreadcrumbItem />
                </n-breadcrumb>
            </template>
        </n-page-header>

        <n-text>Please use Console Window to run your code, api to access api server, data to access requested data, log to access running log.</n-text>
    </n-space>
</template>