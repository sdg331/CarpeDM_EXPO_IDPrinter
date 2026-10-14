import test from "node:test";
import assert from "node:assert/strict";
import { validateComparison, recommendationMarkup } from "../../frontend/js/matching-lab-core.js";

const fixture = () => ({ok:true,experimental:true,externalUpload:false,characterGender:"male",
  face:{count:2,selection:"largest_visible_face",source:"yunet",imageSize:[640,480],box:[.2,.1,.4,.7],landmarks:Array.from({length:5},()=>[.5,.5])},
  sface:{characterId:"char_02",elapsedMs:40,ranking:[2,4,6,8].map(i=>({characterId:`char_0${i}`,score:.1}))},
  ratios:{characterId:"char_04",elapsedMs:1200,distributionCorrected:true,ranking:[4,2,6,8].map(i=>({characterId:`char_0${i}`,distance:1})),landmarks:Array.from({length:478},()=>[.5,.5])}});

test("Comparison validates both rankings against the same requested candidates",()=>{
  assert.equal(validateComparison(fixture(),"male").ratios.characterId,"char_04");
  const female=fixture(); female.ratios.characterId="char_01";
  assert.throws(()=>validateComparison(female,"male"));
  assert.throws(()=>validateComparison(fixture(),"female"));
  const duplicate=fixture(); duplicate.sface.ranking[1]=duplicate.sface.ranking[0];
  assert.throws(()=>validateComparison(duplicate,"male"));
});
test("Malformed landmark results and external transmission flags are rejected",()=>{
  const data=fixture(); data.ratios.landmarks[0]=[NaN,.5];
  assert.throws(()=>validateComparison(data,"male"));
  const external=fixture(); external.externalUpload=true;
  assert.throws(()=>validateComparison(external,"male"));
  const old=fixture(); old.ratios.distributionCorrected=false;
  assert.throws(()=>validateComparison(old,"male"));
});
test("Recommendation markup accepts only the current eight characters and no accuracy percentage",()=>{
  const html=recommendationMarkup(fixture().ratios);
  assert.match(html,/캐릭터 04/); assert.doesNotMatch(html,/%/);
  assert.throws(()=>recommendationMarkup({characterId:'<script>',ranking:[]}));
});
