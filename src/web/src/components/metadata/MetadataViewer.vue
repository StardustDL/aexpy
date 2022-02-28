<script setup lang="ts">
import { NSpace } from 'naive-ui'
import { Product } from '../../models'
import MetadataTimeViewer from './MetadataTimeViewer.vue'
import MetadataTagViewer from './MetadataTagViewer.vue'
import MetadataWordCountViewer from './MetadataWordCountViewer.vue';
import MetadataReadTimeViewer from './MetadataReadTimeViewer.vue';

const props = defineProps<{
    data: Product
}>();

</script>

<template>
    <n-space>
        <MetadataTimeViewer :creation="data.creation"/>
    </n-space>
</template>
