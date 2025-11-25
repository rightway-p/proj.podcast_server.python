import {
  Button,
  FormControl,
  FormLabel,
  HStack,
  Input,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  Select,
  Stack,
  Switch,
  Textarea,
} from '@chakra-ui/react';
import { useEffect, useMemo, useState } from 'react';
import type { CastopodPodcast, JobQuickCreateInput } from '../../api/types';

interface JobCreateModalProps {
  isOpen: boolean;
  onClose: () => void;
  castopodPodcasts: CastopodPodcast[];
  onFetchCastopodPodcasts: () => Promise<void>;
  isFetchingCastopod: boolean;
  onSubmit: (payload: JobQuickCreateInput) => Promise<void>;
}

const defaultForm: JobQuickCreateInput = {
  job_name: '',
  youtube_playlist: '',
  castopod_slug: '',
  castopod_uuid: '',
  should_castopod_upload: true,
  note: '',
  channel_description: '',
};

export function JobCreateModal({
  isOpen,
  onClose,
  castopodPodcasts,
  onFetchCastopodPodcasts,
  isFetchingCastopod,
  onSubmit,
}: JobCreateModalProps) {
  const [form, setForm] = useState<JobQuickCreateInput>(defaultForm);
  const [submitting, setSubmitting] = useState(false);
  const [selectedUuid, setSelectedUuid] = useState<string>('');
  const [slugManuallyEdited, setSlugManuallyEdited] = useState(false);

  const castopodOptions = useMemo(
    () =>
      castopodPodcasts.map((podcast) => ({
        label: `${podcast.title} (${podcast.slug})`,
        value: podcast.uuid,
      })),
    [castopodPodcasts],
  );

  useEffect(() => {
    if (!isOpen) {
      setForm(defaultForm);
      setSelectedUuid('');
      setSlugManuallyEdited(false);
    }
  }, [isOpen]);

  const handleSelectCastopod = (uuid: string) => {
    setSelectedUuid(uuid);
    if (!uuid) {
      setSlugManuallyEdited(false);
      setForm((prev) => ({ ...prev, castopod_uuid: '', castopod_slug: '' }));
      return;
    }
    const match = castopodPodcasts.find((podcast) => podcast.uuid === uuid);
    setForm((prev) => ({
      ...prev,
      castopod_uuid: uuid,
      castopod_slug: slugManuallyEdited ? prev.castopod_slug ?? '' : match?.slug ?? '',
    }));
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      await onSubmit(form);
      setForm(defaultForm);
      onClose();
    } finally {
      setSubmitting(false);
    }
  };

  const isDisabled =
    !form.job_name.trim() || !form.youtube_playlist.trim() || (!form.castopod_slug && !form.castopod_uuid);

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="lg">
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>새 작업 생성</ModalHeader>
        <ModalCloseButton />
        <ModalBody>
          <Stack spacing={4}>
            <FormControl isRequired>
              <FormLabel>작업 이름</FormLabel>
              <Input
                value={form.job_name}
                onChange={(e) => setForm({ ...form, job_name: e.target.value })}
                placeholder="예: 말씀의 식탁"
              />
            </FormControl>
            <FormControl isRequired>
              <FormLabel>YouTube 플레이리스트 URL 또는 ID</FormLabel>
              <Input
                value={form.youtube_playlist}
                onChange={(e) => setForm({ ...form, youtube_playlist: e.target.value })}
                placeholder="https://www.youtube.com/playlist?list=..."
              />
            </FormControl>
            <FormControl>
              <FormLabel>Castopod 채널 선택</FormLabel>
              <HStack align="flex-end" spacing={3}>
                <Select
                  placeholder="목록에서 선택하거나 직접 입력"
                  value={selectedUuid}
                  onChange={(e) => handleSelectCastopod(e.target.value)}
                  flex="1"
                >
                  {castopodOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </Select>
                <Button size="sm" onClick={onFetchCastopodPodcasts} isLoading={isFetchingCastopod}>
                  목록 불러오기
                </Button>
              </HStack>
            </FormControl>
            <FormControl>
              <FormLabel>Castopod 채널 Slug</FormLabel>
              <Input
                value={form.castopod_slug ?? ''}
                onChange={(e) => {
                  setSlugManuallyEdited(true);
                  setForm({ ...form, castopod_slug: e.target.value });
                }}
                placeholder="예: my-podcast"
              />
            </FormControl>
            <FormControl isRequired>
              <FormLabel>Castopod 채널 UUID</FormLabel>
              <Input
                value={form.castopod_uuid ?? ''}
                onChange={(e) => setForm({ ...form, castopod_uuid: e.target.value })}
                placeholder="예: 123e4567-e89b-12d3-a456-426614174000"
              />
            </FormControl>
            <FormControl display="flex" alignItems="center">
              <FormLabel mb="0">Castopod 자동 업로드</FormLabel>
              <Switch
                isChecked={form.should_castopod_upload ?? false}
                onChange={(e) => setForm({ ...form, should_castopod_upload: e.target.checked })}
              />
            </FormControl>
            <FormControl>
              <FormLabel>채널 설명 (선택)</FormLabel>
              <Textarea
                value={form.channel_description ?? ''}
                onChange={(e) => setForm({ ...form, channel_description: e.target.value })}
                placeholder="새로 생성되는 채널 설명"
              />
            </FormControl>
            <FormControl>
              <FormLabel>비고</FormLabel>
              <Textarea
                value={form.note ?? ''}
                onChange={(e) => setForm({ ...form, note: e.target.value })}
                placeholder="추가 노트"
              />
            </FormControl>
          </Stack>
        </ModalBody>
        <ModalFooter>
          <Button variant="ghost" mr={3} onClick={onClose}>
            취소
          </Button>
          <Button colorScheme="purple" onClick={handleSubmit} isLoading={submitting} isDisabled={isDisabled}>
            생성
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}
