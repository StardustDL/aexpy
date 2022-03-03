<script setup lang="ts">
import { NSpace, NDescriptions, NIcon, NDescriptionsItem, NButton, NH6 } from 'naive-ui'
import { ReleaseIcon } from '../icons'
import { Distribution, Product } from '../../models'
import { useStore } from '../../services/store'

const store = useStore();

const props = defineProps<{
    data: Distribution,
}>();

</script>

<template>
    <n-descriptions :column="1">
        <template #header>
            <n-button
                text
                tag="a"
                :href="`https://pypi.org/project/${data.release.project}/${data.release.version}/`"
                target="_blank"
                type="primary"
                style="font-size: x-large;"
            >
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
        <n-descriptions-item>
            <template #label>
                <n-h6 type="info" prefix="bar">Top Level Modules</n-h6>
            </template>
            <n-space vertical>
                <span v-for="item in data.topModules" :key="item">{{ item }}</span>
            </n-space>
        </n-descriptions-item>
        <n-descriptions-item>
            <template #label>
                <n-h6 type="info" prefix="bar">Wheel File</n-h6>
            </template>
            <n-button
                text
                tag="a"
                :href="`${store.state.api.raw.getUrl(data.wheelFile)}`"
                target="_blank"
            >
                {{ data.fileName() }}
            </n-button>
        </n-descriptions-item>
    </n-descriptions>
</template>
