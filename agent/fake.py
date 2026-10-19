"""Canned LLM answers so --dry-run exercises the whole pipeline without an API key."""

from .schemas import Caption, Idea, IdeaList, Scene, Script


class FakeLLM:
    def ask(self, prompt: str, schema):
        if schema is IdeaList:
            return IdeaList(ideas=[
                Idea(title="หมอนใบเก่าของพ่อ", angle="ลูกที่ทำงานหนักจนลืมกลับบ้าน",
                     hook="พ่อไม่เคยบอกว่าคิดถึง จนวันที่ฉันเจอหมอนใบนั้น", hook_score=8,
                     product_category="อุปกรณ์ช่วยการนอน"),
            ])
        if schema is Script:
            lines = [
                "พ่อไม่เคยบอกว่าคิดถึง จนวันที่ฉันเจอหมอนใบนั้น",
                "สามปีที่ฉันทำงานกรุงเทพ ไม่เคยกลับบ้านเลยสักสงกรานต์",
                "วันที่กลับไป ห้องฉันยังสะอาดเหมือนเดิม",
                "บนเตียงมีหมอนใบใหม่ ที่พ่อซื้อไว้ตั้งแต่ปีแรก",
                "พ่อบอกว่า เผื่อลูกกลับมาจะได้นอนสบาย",
                "คืนนี้โทรหาคนที่บ้านหน่อยไหม แล้วเล่าให้ฟังในคอมเมนต์",
            ]
            return Script(title="หมอนใบเก่าของพ่อ", scenes=[
                Scene(narration=t, image_prompt=f"warm cinematic Thai home scene {i}, vertical 9:16, no text")
                for i, t in enumerate(lines)
            ])
        if schema is Caption:
            return Caption(youtube_title="หมอนใบเก่าของพ่อ #เรื่องเล่า",
                           caption="บางคนรักเราโดยไม่เคยพูดออกมา คุณนึกถึงใครอยู่?",
                           hashtags=["เรื่องเล่า", "พ่อ", "ครอบครัว", "shorts", "storytime"],
                           disclosure="ลิงก์ในคลิปนี้เป็นลิงก์ affiliate ช่องได้ค่าคอมเมื่อมีการสั่งซื้อ")
        raise TypeError(schema)
