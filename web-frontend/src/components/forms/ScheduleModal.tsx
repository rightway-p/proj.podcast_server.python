import {
  Button,
  FormControl,
  FormLabel,
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
} from '@chakra-ui/react';
import { useState } from 'react';
import type { ScheduleFormInput, Playlist } from '../../api/types';

interface ScheduleModalProps {
  isOpen: boolean;
  onClose: () => void;
  playlists: Playlist[];
  onSubmit: (payload: ScheduleFormInput) => Promise<void>;
}

export function ScheduleModal({ isOpen, onClose, playlists, onSubmit }: ScheduleModalProps) {
  const [form, setForm] = useState<ScheduleFormInput>({
    playlist_id: playlists[0]?.id ?? 0,
    cron_expression: '0 7,19 * * *',
    timezone: 'Asia/Seoul',
    is_active: true,
  });
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      await onSubmit(form);
      setForm({ ...form, cron_expression: '0 7,19 * * *', playlist_id: playlists[0]?.id ?? 0 });
      onClose();
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="lg">
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>스케줄 추가</ModalHeader>
        <ModalCloseButton />
        <ModalBody>
          <Stack spacing={4}>
            <FormControl isRequired>
              <FormLabel>플레이리스트</FormLabel>
              <Select value={form.playlist_id} onChange={(e) => setForm({ ...form, playlist_id: Number(e.target.value) })}>
                {playlists.map((playlist) => (
                  <option key={playlist.id} value={playlist.id}>
                    {playlist.title || playlist.youtube_playlist_id}
                  </option>
                ))}
              </Select>
            </FormControl>
            <FormControl isRequired>
              <FormLabel>크론 표현식</FormLabel>
              <Input value={form.cron_expression} onChange={(e) => setForm({ ...form, cron_expression: e.target.value })} />
            </FormControl>
            <FormControl>
              <FormLabel>타임존</FormLabel>
              <Input value={form.timezone} onChange={(e) => setForm({ ...form, timezone: e.target.value })} />
            </FormControl>
            <FormControl display="flex" alignItems="center">
              <FormLabel mb="0">활성</FormLabel>
              <Switch isChecked={form.is_active ?? true} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} />
            </FormControl>
          </Stack>
        </ModalBody>
        <ModalFooter>
          <Button variant="ghost" mr={3} onClick={onClose}>
            취소
          </Button>
          <Button colorScheme="purple" onClick={handleSubmit} isLoading={submitting} isDisabled={!playlists.length}>
            생성
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}
