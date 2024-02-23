<script setup lang="ts">
import { NFlex, NDescriptions, NIcon, NDescriptionsItem, NButton, NH6, NText } from 'naive-ui'
import { PackageIcon } from '../icons'
import { Distribution, Product } from '../../models'
import { useStore } from '../../services/store'
import { apiUrl } from '../../services/utils'
import ApiEntryLink from '../links/ApiEntryLink.vue';

defineProps<{
    data: Distribution,
}>();

</script>

<template>
    <n-flex vertical>
        <n-descriptions size="large" bordered>
            <template #header>
                <n-button text tag="a" :href="`https://pypi.org/project/${data.release.project}/${data.release.version}/`"
                    target="_blank" type="primary" style="font-size: x-large;">
                    <template #icon>
                        <n-icon size="large" :component="PackageIcon" />
                    </template>
                    {{ data.release }}
                </n-button>
            </template>
            <n-descriptions-item>
                <template #label>
                    <n-text type="primary">Python Version</n-text>
                </template>
                {{ data.pyversion }}
            </n-descriptions-item>
            <n-descriptions-item v-if="data.fileName()">
                <template #label>
                    <n-text type="primary">Wheel File</n-text>
                </template>
                <n-text>{{ data.fileName() }}</n-text>
            </n-descriptions-item>
            <n-descriptions-item>
                <template #label>
                    <n-text type="primary">Source Count</n-text>
                </template>
                {{ data.fileCount }} files ({{ data.fileSize }} bytes, {{ data.locCount }} LOCs)
            </n-descriptions-item>
            <n-descriptions-item>
                <template #label>
                    <n-text type="primary">Top Level Modules</n-text>
                </template>
                <n-flex>
                    <ApiEntryLink :url="apiUrl(data.release)" v-for="item in data.topModules" :key="item" :entry="item">{{
                        item }}</ApiEntryLink>
                </n-flex>
            </n-descriptions-item>
            <n-descriptions-item v-if="data.dependencies.length > 0">
                <template #label>
                    <n-text type="primary">Dependencies</n-text>
                </template>
                <n-flex>
                    <n-button v-for="item in data.dependencies" text tag="a" :href="`https://pypi.org/project/${item}`"
                        target="_blank">
                        <template #icon>
                            <n-icon size="large" :component="PackageIcon" />
                        </template>
                        {{ item }}
                    </n-button>
                </n-flex>
            </n-descriptions-item>
        </n-descriptions>
    </n-flex>
</template>
