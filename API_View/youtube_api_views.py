# ---------- ⬇️ 모델 호출 ----------
from streaming_site_list.youtube.models import YouTubeSongViewCount
# ---------- ⬇️ Serializer 호출 ----------
from streaming_site_list.youtube.api_serializers import YouTubeSongViewCountSerializer
# ---------- ⬇️ crawler 함수 호출 ----------
from crawling_view.youtube_crawler_views import YouTubeSongCrawler, save_each_to_csv, save_to_db
from celery_setup.task_setup.youtube_tasks import (
    youtube_crawl_rhoonart,
)
# ---------- ⬇️ Swagger를 위하여 ----------
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
# ---------- ⬇️ DRF 패키지 호출 ----------
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import logging


logger = logging.getLogger(__name__)

# ---------- ⬇️ API 함수 정의 ----------
class YouTubeSongViewCountAPIView(APIView):
    @swagger_auto_schema(
        operation_summary="고객사별 유튜브 노래 조회수 및 업로드일 크롤링",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'urls': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING),
                    description="크롤링할 유튜브 동영상 ID 목록"
                ),
                'company_name': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="크롤링할 고객사 명(영어로 입력해주세요. 예: rhoonart)"
                ),
                'service_name': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="크롤링할 서비스 명(영어로 입력해주세요. 예: youtube)"
                ),
                'immediate': openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description="즉시 크롤링 실행 여부 (기본값: False)",
                    default=False
                )
            },
            required=['urls', 'company_name', 'service_name'],
            example={
                'urls': ["https://www.youtube.com/watch?v=Sv2mIvMwrSY", "https://www.youtube.com/watch?v=R1CZTJ8hW0s"],
                'company_name': "rhoonart",
                'immediate': False
            }
        ),
    )
    def post(self, request):
        urls = request.data.get('urls', [])
        company_name = request.data.get('company_name', 'default')
        service_name = request.data.get('service_name', 'youtube')
        immediate = request.data.get('immediate', False)

        if not urls:
            return Response(
                {'error': 'urls 필드가 필요합니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            if immediate:
                # 즉시 실행
                results = YouTubeSongCrawler(urls)
                save_each_to_csv(results, company_name, service_name)
                save_to_db(results)
                return Response({
                    'message': '크롤링이 즉시 실행되었습니다.',
                    'results': results
                }, status=status.HTTP_200_OK)
            else:
                # 고객사별로 Celery task 나누기
                if company_name == "rhoonart":
                    youtube_crawl_rhoonart.delay(urls, company_name)
                # elif company_name == "":
                #     pass
                else:
                    return Response({
                        'error': f'알 수 없는 company_name: {company_name}'
                    }, status=status.HTTP_400_BAD_REQUEST)

                return Response({
                    'message': '크롤링 작업이 성공적으로 예약되었습니다.',
                    'task_info': {
                        'song_count': len(urls)
                    }
                }, status=status.HTTP_202_ACCEPTED)

        except Exception as e:
            return Response({
                'error': f'크롤링 작업 처리 중 오류가 발생했습니다: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        operation_summary="유튜브 노래 조회수 조회",
        responses={200: YouTubeSongViewCountSerializer(many=True)}
    )
    def get(self, request):
        queryset = YouTubeSongViewCount.objects.all().order_by('-extracted_date') # 크롤링 한 날짜의 최신순으로 정렬
        serializer = YouTubeSongViewCountSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


    '''===================== ⬇️ 유튜브 노래 조회수 정보 수정 API ====================='''
    @swagger_auto_schema(
        operation_summary="유튜브 노래 조회수 정보 수정",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'id': openapi.Schema(type=openapi.TYPE_INTEGER, description="수정할 객체의 ID"),
                'video_id': openapi.Schema(type=openapi.TYPE_STRING, description="수정할 객체의 video_id"),
                'view_count': openapi.Schema(type=openapi.TYPE_INTEGER, description="수정할 조회수 값"),
                'extracted_date': openapi.Schema(type=openapi.TYPE_STRING, format='date', description="수정할 추출 날짜 (YYYY-MM-DD)")
            },
            required=[],
            example={
                'video_id': 'Sv2mIvMwrSY',
                'view_count': 123456,
                'extracted_date': '2024-06-01'
            }
        ),
    )
    def put(self, request):
        obj_id = request.data.get('id')
        video_id = request.data.get('video_id')
        if not obj_id and not video_id:
            return Response({'error': 'id 또는 video_id 필드가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            if obj_id:
                obj = YouTubeSongViewCount.objects.get(id=obj_id)
            else:
                obj = YouTubeSongViewCount.objects.get(video_id=video_id)
        except YouTubeSongViewCount.DoesNotExist:
            return Response({'error': '해당 id 또는 video_id의 객체가 존재하지 않습니다.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = YouTubeSongViewCountSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': '수정이 완료되었습니다.', 'data': serializer.data}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    '''===================== ⬇️ 유튜브 노래 조회수 정보 삭제 API ====================='''
    @swagger_auto_schema(
        operation_summary="유튜브 노래 조회수 정보 삭제",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'id': openapi.Schema(type=openapi.TYPE_INTEGER, description="삭제할 객체의 ID"),
                'video_id': openapi.Schema(type=openapi.TYPE_STRING, description="삭제할 객체의 video_id")
            },
            required=[],
            example={
                'video_id': 'Sv2mIvMwrSY'
            }
        ),
    )
    def delete(self, request):
        obj_id = request.data.get('id')
        video_id = request.data.get('video_id')
        if not obj_id and not video_id:
            return Response({'error': 'id 또는 video_id 필드가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            if obj_id:
                obj = YouTubeSongViewCount.objects.get(id=obj_id)
            else:
                obj = YouTubeSongViewCount.objects.get(video_id=video_id)
            obj.delete()
            return Response({'message': '삭제가 완료되었습니다.'}, status=status.HTTP_200_OK)
        except YouTubeSongViewCount.DoesNotExist:
            return Response({'error': '해당 id 또는 video_id의 객체가 존재하지 않습니다.'}, status=status.HTTP_404_NOT_FOUND)