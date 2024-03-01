<script setup lang="ts">
import { NFlex, NTooltip } from 'naive-ui'
import { Product } from '../../models'
import MetadataTimeViewer from './MetadataTimeViewer.vue'
import MetadataDurationViewer from './MetadataDurationViewer.vue'
import MetadataStateViewer from './MetadataStateViewer.vue'

defineProps<{
    data: Product
}>();

</script>

<template>
    <n-flex v-if="data">
        <n-tooltip>
            <template #trigger>
                <MetadataStateViewer :state="data.state" />
            </template>
            {{ data.producer }}
        </n-tooltip>
        <MetadataTimeViewer :creation="data.creation" />
        <MetadataDurationViewer :duration="data.duration" />
    </n-flex>
</template>
