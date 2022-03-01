<script setup lang="ts">
import { NSpace, NDescriptions, NDescriptionsItem } from 'naive-ui'
import { Distribution, Product } from '../../models'
import MetadataTimeViewer from './MetadataTimeViewer.vue'
import MetadataDurationViewer from './MetadataDurationViewer.vue'
import MetadataSuccessViewer from './MetadataSuccessViewer.vue'

const props = defineProps<{
    data: Distribution,
    title?: string,
}>();

</script>

<template>
    <n-descriptions :title="title ? title : 'Distribution Information'">
        <n-descriptions-item>
            <template #label>Python Version</template>
            {{ data.pyversion }}
        </n-descriptions-item>
        <n-descriptions-item>
            <template #label>Top Modules</template>
            <n-space vertical>
                <span v-for="item in data.topModules">{{ item }}</span>
            </n-space>
        </n-descriptions-item>
    </n-descriptions>
</template>
