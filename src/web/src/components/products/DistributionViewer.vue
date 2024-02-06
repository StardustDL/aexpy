<script setup lang="ts">
import { NSpace, NDescriptions, NIcon, NDescriptionsItem, NButton, NH6, NText } from 'naive-ui'
import { ReleaseIcon } from '../icons'
import { Distribution, Product } from '../../models'
import { useStore } from '../../services/store'
import ApiEntryLink from '../metadata/ApiEntryLink.vue';

defineProps<{
    data: Distribution,
}>();

</script>

<template>
    <n-space vertical>
        <n-descriptions>
            <template #header>
                <n-button text tag="a" :href="`https://pypi.org/project/${data.release.project}/${data.release.version}/`"
                    target="_blank" type="primary" style="font-size: x-large;">
                    <template #icon>
                        <n-icon size="large">
                            <ReleaseIcon />
                        </n-icon>
                    </template>
                    {{ data.release }}
                </n-button>
            </template>
            <n-descriptions-item>
                <template #label>
                    <n-h6 type="info" prefix="bar">Python Version</n-h6>
                </template>
                {{ data.pyversion }}
            </n-descriptions-item>
            <n-descriptions-item v-if="data.fileName()">
                <template #label>
                    <n-h6 type="info" prefix="bar">Wheel File</n-h6>
                </template>
                <n-text>{{ data.fileName() }}</n-text>
            </n-descriptions-item>
            <n-descriptions-item>
                <template #label>
                    <n-h6 type="info" prefix="bar">Source Count</n-h6>
                </template>
                {{ data.fileCount }} files ({{ data.fileSize }} bytes, {{ data.locCount }} LOCs)
            </n-descriptions-item>
        </n-descriptions>
        <n-descriptions :column="1">
            <n-descriptions-item>
                <template #label>
                    <n-h6 type="info" prefix="bar">Top Level Modules</n-h6>
                </template>
                <n-space>
                    <ApiEntryLink :url="`/apis/${data.release.toString()}/`" v-for="item in data.topModules" :key="item"
                        :entry="item">{{ item }}</ApiEntryLink>
                </n-space>
            </n-descriptions-item>
            <n-descriptions-item v-if="data.dependencies.length > 0">
                <template #label>
                    <n-h6 type="info" prefix="bar">Dependencies</n-h6>
                </template>
                <n-space>
                    <n-button v-for="item in data.dependencies" text tag="a" :href="`https://pypi.org/project/${item}`"
                        target="_blank">
                        <template #icon>
                            <n-icon size="large">
                                <ReleaseIcon />
                            </n-icon>
                        </template>
                        {{ item }}
                    </n-button>
                </n-space>
            </n-descriptions-item>
        </n-descriptions>
    </n-space>
</template>
