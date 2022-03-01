<script setup lang="ts">
import { NSpace } from 'naive-ui'
import { Product } from '../../models'
import MetadataTimeViewer from './MetadataTimeViewer.vue'
import MetadataDurationViewer from './MetadataDurationViewer.vue'
import MetadataSuccessViewer from './MetadataSuccessViewer.vue'

const props = defineProps<{
    data: Product
}>();

</script>

<template>
    <n-space v-if="data">
        <MetadataSuccessViewer :success="data.success" />
        <MetadataTimeViewer :creation="data.creation" />
        <MetadataDurationViewer :duration="data.duration" />
    </n-space>
</template>
