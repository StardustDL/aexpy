<script setup lang="ts">
import { NSpace, NDescriptions, NDescriptionsItem} from 'naive-ui'
import { VerifyData } from '../../models/difference'

const props = defineProps<{
    data: VerifyData
}>();

</script>

<template>
    <n-descriptions :column="1" v-if="data.verifier.length > 0">
        <n-descriptions-item>
            <template #label>Verifier</template>
            {{ data.verifier }}
        </n-descriptions-item>
        <n-descriptions-item v-if="data.message.length > 0">
            <template #label>Message</template>
            {{ data.message }}
        </n-descriptions-item>
    </n-descriptions>
</template>
